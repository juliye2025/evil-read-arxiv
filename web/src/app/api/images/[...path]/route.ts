import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

const IMAGES_DIR = path.join(process.cwd(), "..", "data", "paper_images");

const MIME_TYPES: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

export async function GET(
  _req: NextRequest,
  ctx: RouteContext<"/api/images/[...path]">
) {
  const params = await ctx.params;
  const segments = params.path;

  // Validate path segments to prevent directory traversal
  for (const seg of segments) {
    if (seg.includes("..") || seg.includes("/") || seg.includes("\\")) {
      return new NextResponse("Forbidden", { status: 403 });
    }
  }

  const filePath = path.join(IMAGES_DIR, ...segments);

  try {
    const data = await fs.readFile(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || "application/octet-stream";

    return new NextResponse(data, {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=86400",
      },
    });
  } catch {
    return new NextResponse("Not Found", { status: 404 });
  }
}
