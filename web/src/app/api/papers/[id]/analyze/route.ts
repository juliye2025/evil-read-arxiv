import { NextRequest, NextResponse } from "next/server";
import { createAnthropicClientWithSettings } from "@/lib/anthropic";
import { getCachedAnalysis, cacheAnalysis, getResearchConfig } from "@/lib/data";
import type { PaperAnalysis } from "@/lib/types";
import { type Language, prompts } from "@/lib/i18n";

export async function GET(
  _req: NextRequest,
  ctx: RouteContext<"/api/papers/[id]/analyze">
) {
  const { id } = await ctx.params;
  const arxivId = decodeURIComponent(id);

  try {
    const config = await getResearchConfig();
    const lang: Language = config.language === "en" ? "en" : "zh";
    const cacheId = `${arxivId}_${lang}`;

    const cached = await getCachedAnalysis(cacheId);
    if (cached) {
      return NextResponse.json(cached);
    }

    const { client, model } = await createAnthropicClientWithSettings();

    // Fetch paper abstract from arXiv API
    const arxivRes = await fetch(
      `http://export.arxiv.org/api/query?id_list=${arxivId}`
    );
    const xml = await arxivRes.text();

    const titleMatch = xml.match(/<title[^>]*>([\s\S]*?)<\/title>/g);
    const title = titleMatch && titleMatch.length > 1
      ? titleMatch[1].replace(/<\/?title[^>]*>/g, "").trim()
      : "";

    const summaryMatch = xml.match(/<summary[^>]*>([\s\S]*?)<\/summary>/);
    const abstract = summaryMatch
      ? summaryMatch[1].trim()
      : "";

    if (!abstract) {
      return NextResponse.json(
        { error: "Could not fetch paper abstract" },
        { status: 404 }
      );
    }

    const response = await client.messages.create({
      model,
      max_tokens: 2048,
      messages: [
        {
          role: "user",
          content: prompts.analyze[lang](title, abstract),
        },
      ],
    });

    const text =
      response.content[0].type === "text" ? response.content[0].text : "";

    let analysis: PaperAnalysis;
    try {
      // Try direct parse first
      analysis = JSON.parse(text);
    } catch {
      // Try extracting JSON from markdown code block
      const codeBlockMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
      const jsonStr = codeBlockMatch
        ? codeBlockMatch[1].trim()
        : (text.match(/\{[\s\S]*\}/) || [""])[0];

      if (jsonStr) {
        try {
          analysis = JSON.parse(jsonStr);
        } catch {
          // Last resort: extract fields manually with regex
          const extract = (key: string) => {
            const m = text.match(new RegExp(`"${key}"\\s*:\\s*"([^"]*(?:\\\\"[^"]*)*)"`));
            return m ? m[1].replace(/\\"/g, '"') : "";
          };
          analysis = {
            contribution: extract("contribution"),
            innovation: extract("innovation"),
            method: extract("method"),
            results: extract("results"),
          };
          if (!analysis.contribution && !analysis.innovation) {
            throw new Error("Failed to parse analysis response");
          }
        }
      } else {
        throw new Error("Failed to parse analysis response");
      }
    }

    await cacheAnalysis(cacheId, analysis);
    return NextResponse.json(analysis);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Analysis failed: ${message}` },
      { status: 500 }
    );
  }
}
