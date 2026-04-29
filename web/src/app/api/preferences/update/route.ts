import { NextResponse } from "next/server";
import { createAnthropicClientWithSettings } from "@/lib/anthropic";
import {
  getFeedback,
  getPreferences,
  savePreferences,
  getResearchConfig,
  saveResearchConfig,
} from "@/lib/data";
import type { PreferenceUpdateResult } from "@/lib/types";

export async function POST() {
  try {
    const feedback = await getFeedback();
    const currentPrefs = await getPreferences();
    const config = await getResearchConfig();

    if (feedback.feedback.length === 0) {
      return NextResponse.json({
        success: true,
        changes: {
          added_keywords: [],
          removed_keywords: [],
          priority_changes: [],
          summary: "No feedback data to analyze.",
        },
      } satisfies PreferenceUpdateResult);
    }

    const lastUpdate = currentPrefs.last_updated;
    const recentFeedback = lastUpdate
      ? feedback.feedback.filter((f) => f.date >= lastUpdate)
      : feedback.feedback;

    if (recentFeedback.length === 0) {
      return NextResponse.json({
        success: true,
        changes: {
          added_keywords: [],
          removed_keywords: [],
          priority_changes: [],
          summary: "No new feedback since last update.",
        },
      } satisfies PreferenceUpdateResult);
    }

    const { client, model } = await createAnthropicClientWithSettings();

    const prompt = `You are a research interest analyzer. Based on the user's paper feedback, analyze their preference patterns and suggest updates to their research interest configuration.

## Current Research Domains
${JSON.stringify(config.research_domains, null, 2)}

## Current Preference Weights
${JSON.stringify(currentPrefs, null, 2)}

## Recent Feedback (${recentFeedback.length} papers)
${recentFeedback
  .map(
    (f) =>
      `- [${f.rating.toUpperCase()}] "${f.title}" (domain: ${f.domain}, keywords: ${f.keywords.join(", ")}, categories: ${f.categories.join(", ")})`
  )
  .join("\n")}

## Instructions
Analyze the feedback patterns and output a JSON object with these exact fields:
{
  "keyword_weights": { "keyword": weight_number },
  "domain_weights": { "domain_name": weight_number },
  "category_weights": { "category": weight_number },
  "priority_changes": [{ "domain": "name", "old": current_priority, "new": suggested_priority }],
  "added_keywords": ["new keywords to add to relevant domains"],
  "removed_keywords": ["keywords user consistently dislikes"],
  "summary": "2-3 sentence summary in the user's language (${config.language === "zh" ? "Chinese" : "English"})"
}

Only output the JSON object, no markdown fences or explanation.`;

    const response = await client.messages.create({
      model,
      max_tokens: 2048,
      messages: [{ role: "user", content: prompt }],
    });

    const text =
      response.content[0].type === "text" ? response.content[0].text : "";
    const changes = JSON.parse(text);

    const newPrefs = { ...currentPrefs };
    newPrefs.keyword_weights = {
      ...newPrefs.keyword_weights,
      ...changes.keyword_weights,
    };
    newPrefs.domain_weights = {
      ...newPrefs.domain_weights,
      ...changes.domain_weights,
    };
    newPrefs.category_weights = {
      ...newPrefs.category_weights,
      ...changes.category_weights,
    };
    newPrefs.last_updated = new Date().toISOString().slice(0, 10);
    newPrefs.update_history.push({
      date: newPrefs.last_updated,
      summary: changes.summary,
      changes,
    });

    await savePreferences(newPrefs);

    if (changes.priority_changes?.length > 0) {
      for (const change of changes.priority_changes) {
        if (config.research_domains[change.domain]) {
          config.research_domains[change.domain].priority = change.new;
        }
      }
      await saveResearchConfig(config);
    }

    if (changes.added_keywords?.length > 0) {
      const domains = Object.entries(config.research_domains);
      if (domains.length > 0) {
        const topDomain = domains.sort(
          (a, b) => b[1].priority - a[1].priority
        )[0];
        const existing = new Set(topDomain[1].keywords);
        for (const kw of changes.added_keywords) {
          if (!existing.has(kw)) {
            topDomain[1].keywords.push(kw);
          }
        }
        await saveResearchConfig(config);
      }
    }

    return NextResponse.json({
      success: true,
      changes: {
        added_keywords: changes.added_keywords || [],
        removed_keywords: changes.removed_keywords || [],
        priority_changes: changes.priority_changes || [],
        summary: changes.summary || "",
      },
    } satisfies PreferenceUpdateResult);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to update preferences: ${message}` },
      { status: 500 }
    );
  }
}
