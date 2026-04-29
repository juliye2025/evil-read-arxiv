import { NextResponse } from "next/server";
import { getPreferences } from "@/lib/data";

export async function GET() {
  try {
    const prefs = await getPreferences();
    return NextResponse.json(prefs);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to read preferences: ${message}` },
      { status: 500 }
    );
  }
}
