import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import { promises as fs } from "fs";
import { getCachedImages, cacheImages, getImagesDir } from "@/lib/data";
import type { PaperImage } from "@/lib/types";

const execAsync = promisify(exec);
const PROJECT_ROOT = path.join(process.cwd(), "..");
const SCRIPT_PATH = path.join(
  PROJECT_ROOT,
  "extract-paper-images",
  "scripts",
  "extract_images.py"
);

export async function GET(
  _req: NextRequest,
  ctx: RouteContext<"/api/papers/[id]/images">
) {
  const { id } = await ctx.params;
  const arxivId = decodeURIComponent(id);

  try {
    const cached = await getCachedImages(arxivId);
    if (cached) {
      return NextResponse.json(cached);
    }

    const imagesDir = getImagesDir(arxivId);
    await fs.mkdir(imagesDir, { recursive: true });
    const indexFile = path.join(imagesDir, "raw_index.md");

    try {
      await execAsync(
        `python3 "${SCRIPT_PATH}" "${arxivId}" "${imagesDir}" "${indexFile}"`,
        { timeout: 120000, cwd: PROJECT_ROOT }
      );
    } catch (err) {
      console.error("Image extraction failed:", err);
      const emptyResult: PaperImage[] = [];
      await cacheImages(arxivId, emptyResult);
      return NextResponse.json(emptyResult);
    }

    // Read extracted files
    const files = await fs.readdir(imagesDir);
    const imageFiles = files.filter((f) => {
      const ext = f.toLowerCase();
      return (
        (ext.endsWith(".png") ||
          ext.endsWith(".jpg") ||
          ext.endsWith(".jpeg")) &&
        f !== "index.json"
      );
    });

    const safe = arxivId.replace(/[^a-zA-Z0-9._-]/g, "_");
    const images: PaperImage[] = imageFiles.map((filename) => ({
      filename,
      url: `/api/images/${safe}/${filename}`,
      source: "arxiv",
    }));

    await cacheImages(arxivId, images);
    return NextResponse.json(images);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Image extraction failed: ${message}` },
      { status: 500 }
    );
  }
}
