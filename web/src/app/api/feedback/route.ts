import { NextRequest, NextResponse } from "next/server";
import { addFeedback } from "@/lib/data";
import type { FeedbackEntry } from "@/lib/types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { arxiv_id, title, rating, date, domain, keywords, categories } =
      body;

    if (!arxiv_id || !rating || !date) {
      return NextResponse.json(
        { error: "arxiv_id, rating, and date are required" },
        { status: 400 }
      );
    }

    if (!["like", "neutral", "dislike"].includes(rating)) {
      return NextResponse.json(
        { error: "rating must be like, neutral, or dislike" },
        { status: 400 }
      );
    }

    const entry: FeedbackEntry = {
      arxiv_id,
      title: title || "",
      rating,
      date,
      domain: domain || "",
      keywords: keywords || [],
      categories: categories || [],
    };

    const unprocessedCount = await addFeedback(entry);

    return NextResponse.json({
      success: true,
      should_update_preferences: unprocessedCount >= 10,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to save feedback: ${message}` },
      { status: 500 }
    );
  }
}
