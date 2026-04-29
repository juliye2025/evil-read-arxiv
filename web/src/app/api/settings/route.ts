import { NextRequest, NextResponse } from "next/server";
import { getResearchConfig, saveResearchConfig } from "@/lib/data";
import { getApiSettings, saveApiSettings } from "@/lib/anthropic";
import type { AppSettings } from "@/lib/types";

export async function GET() {
  try {
    const research = await getResearchConfig();
    const apiSettings = await getApiSettings();

    const settings: AppSettings = {
      claude: {
        model: apiSettings.model || "claude-sonnet-4-6",
        api_key: apiSettings.api_key || "",
        max_tokens: 4096,
      },
      research,
      general: {
        language: research.language || "zh",
        daily_paper_count: 10,
        obsidian_sync: !!research.vault_path,
        semantic_scholar_api_key: research.semantic_scholar_api_key || "",
      },
    };

    // Mask API key for display
    if (settings.claude.api_key) {
      const key = settings.claude.api_key;
      settings.claude.api_key =
        key.slice(0, 7) + "..." + key.slice(-4);
    }

    return NextResponse.json(settings);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to read settings: ${message}` },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();

    if (body.research) {
      await saveResearchConfig(body.research);
    }

    if (body.claude) {
      const current = await getApiSettings();
      const updated = { ...current };

      if (body.claude.model) {
        updated.model = body.claude.model;
      }
      if (body.claude.api_key && !body.claude.api_key.includes("...")) {
        updated.api_key = body.claude.api_key;
      }
      if (body.claude.base_url) {
        updated.base_url = body.claude.base_url;
      }

      await saveApiSettings(updated);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to save settings: ${message}` },
      { status: 500 }
    );
  }
}
