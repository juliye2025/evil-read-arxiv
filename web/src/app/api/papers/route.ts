import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { createAnthropicClientWithSettings } from "@/lib/anthropic";
import {
  getCachedPapers,
  cachePapers,
  getFeedback,
  mergeFeedback,
  getResearchConfig,
  saveResearchConfig,
} from "@/lib/data";
import { searchPapers } from "@/lib/python-bridge";
import path from "path";
import type { Paper } from "@/lib/types";
import { type Language, prompts } from "@/lib/i18n";

async function generateSummary(
  paper: Paper,
  client: Anthropic,
  model: string,
  lang: Language
): Promise<string> {
  try {
    const response = await client.messages.create({
      model,
      max_tokens: 512,
      messages: [
        {
          role: "user",
          content: prompts.summary[lang](
            paper.title,
            paper.original_abstract || paper.summary
          ),
        },
      ],
    });
    const text =
      response.content[0].type === "text" ? response.content[0].text : "";
    return text.trim();
  } catch (err) {
    console.error(`Summary generation failed for ${paper.arxiv_id}:`, err);
    return "";
  }
}

async function batchGenerateSummaries(
  papers: Paper[],
  client: Anthropic,
  model: string,
  lang: Language
): Promise<Paper[]> {
  const CONCURRENCY = 5;
  const results = [...papers];

  for (let i = 0; i < results.length; i += CONCURRENCY) {
    const batch = results.slice(i, i + CONCURRENCY);
    const summaries = await Promise.allSettled(
      batch.map((p) => generateSummary(p, client, model, lang))
    );

    summaries.forEach((result, idx) => {
      const paperIdx = i + idx;
      const chineseSummary =
        result.status === "fulfilled" && result.value
          ? result.value
          : "";
      if (chineseSummary) {
        results[paperIdx] = {
          ...results[paperIdx],
          original_abstract: results[paperIdx].summary,
          summary: chineseSummary,
        };
      } else {
        results[paperIdx] = {
          ...results[paperIdx],
          original_abstract: results[paperIdx].summary,
        };
      }
    });
  }

  return results;
}

async function maybeAddResearchDomain(
  focus: string,
  papers: Paper[],
  client: Anthropic,
  model: string,
  lang: Language
): Promise<void> {
  try {
    const config = await getResearchConfig();
    const existingDomains = Object.keys(config.research_domains);

    // Check if focus already matches an existing domain
    const focusLower = focus.toLowerCase();
    const alreadyExists = existingDomains.some(
      (d) => d.toLowerCase().includes(focusLower) || focusLower.includes(d.toLowerCase())
    );
    if (alreadyExists) return;

    // Use Claude to generate a domain config for this new interest
    const sampleTitles = papers
      .slice(0, 5)
      .map((p) => p.title)
      .join("\n");

    const response = await client.messages.create({
      model,
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: prompts.domain[lang](focus, sampleTitles),
        },
      ],
    });

    const text =
      response.content[0].type === "text" ? response.content[0].text : "";
    let domainConfig: { domain_name: string; keywords: string[]; arxiv_categories: string[] };
    try {
      domainConfig = JSON.parse(text);
    } catch {
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (!jsonMatch) return;
      domainConfig = JSON.parse(jsonMatch[0]);
    }

    if (!domainConfig.domain_name || !domainConfig.keywords?.length) return;

    // Add to config
    config.research_domains[domainConfig.domain_name] = {
      keywords: domainConfig.keywords,
      arxiv_categories: domainConfig.arxiv_categories || [],
      priority: 5,
    };

    await saveResearchConfig(config);
    console.log(`Added new research domain: ${domainConfig.domain_name}`);
  } catch (err) {
    console.warn("Failed to auto-add research domain:", err instanceof Error ? err.message : err);
  }
}

async function translateFocusToEnglish(
  focus: string,
  client: Anthropic,
  model: string,
  lang: Language
): Promise<string> {
  if (/^[\x00-\x7F\s]+$/.test(focus)) return focus;

  try {
    const response = await client.messages.create({
      model,
      max_tokens: 200,
      messages: [
        {
          role: "user",
          content: prompts.translateFocus[lang](focus),
        },
      ],
    });
    const text =
      response.content[0].type === "text" ? response.content[0].text.trim() : "";
    return text || focus;
  } catch {
    return focus;
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const date =
    searchParams.get("date") || new Date().toISOString().slice(0, 10);
  const focus = searchParams.get("focus") || "";
  const range = searchParams.get("range") || ""; // "week" | "month" | ""

  const days = range === "week" ? 7 : range === "month" ? 30 : 1;

  try {
    const config = await getResearchConfig();
    const lang: Language = (config.language === "en" ? "en" : "zh");

    const cacheKey = focus
      ? `${date}_focus_${simpleHash(focus)}_${range || "day"}_${lang}`
      : `${date}_${range || "day"}_${lang}`;

    let cached = await getCachedPapers(cacheKey);
    if (!cached) {
      const configPath = path.join(process.cwd(), "..", "config.yaml");
      const topN = focus ? 20 : 10;

      // Translate Chinese focus to English keywords for arXiv search
      let searchFocus = focus;
      let client: Anthropic | null = null;
      let model = "claude-sonnet-4-6";
      if (focus) {
        try {
          const resolved = await createAnthropicClientWithSettings();
          client = resolved.client;
          model = resolved.model;
          searchFocus = await translateFocusToEnglish(focus, client, model, lang);
          console.log(`Focus translated: "${focus}" → "${searchFocus}"`);
        } catch {
          searchFocus = focus;
        }
      }

      const focusArgs = searchFocus ? ["--focus", searchFocus] : [];
      const papers = await searchPapers(date, configPath, topN, focusArgs, days);

      let summarizedPapers = papers.map((p) => ({
        ...p,
        original_abstract: p.summary,
      }));

      try {
        if (!client) {
          const resolved = await createAnthropicClientWithSettings();
          client = resolved.client;
          model = resolved.model;
        }
        summarizedPapers = await batchGenerateSummaries(papers, client, model, lang);

        // Auto-add new research domain if this is a focus search with results
        if (focus && summarizedPapers.length > 0) {
          maybeAddResearchDomain(focus, papers, client, model, lang).catch(() => {});
        }
      } catch (err) {
        console.warn("Skipping AI summaries:", err instanceof Error ? err.message : err);
      }

      cached = {
        date,
        papers: summarizedPapers,
        total: summarizedPapers.length,
      };
      await cachePapers(cacheKey, cached);
    }

    const feedback = await getFeedback();
    const papersWithFeedback = mergeFeedback(cached.papers, feedback);

    return NextResponse.json({
      date: cached.date,
      papers: papersWithFeedback,
      total: papersWithFeedback.length,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to fetch papers: ${message}` },
      { status: 500 }
    );
  }
}

function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}
