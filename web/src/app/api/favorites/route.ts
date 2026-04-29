import { NextRequest, NextResponse } from "next/server";
import {
  getFavoritePapers,
  getFavoriteFolders,
  saveFavoriteFolders,
  removeFavorite,
} from "@/lib/data";

// GET — return papers + folders
export async function GET() {
  try {
    const [papers, foldersData] = await Promise.all([
      getFavoritePapers(),
      getFavoriteFolders(),
    ]);
    return NextResponse.json({ papers, folders: foldersData.folders });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// POST — create or rename folder
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, id, name } = body as {
      action: "create" | "rename" | "delete_folder";
      id?: string;
      name?: string;
    };

    const data = await getFavoriteFolders();

    if (action === "create") {
      if (!name) return NextResponse.json({ error: "name required" }, { status: 400 });
      const newId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      data.folders.push({ id: newId, name, paperIds: [] });
      await saveFavoriteFolders(data);
      return NextResponse.json({ success: true, folder: data.folders.at(-1) });
    }

    if (action === "rename") {
      if (!id || !name) return NextResponse.json({ error: "id and name required" }, { status: 400 });
      const folder = data.folders.find((f) => f.id === id);
      if (!folder) return NextResponse.json({ error: "folder not found" }, { status: 404 });
      folder.name = name;
      await saveFavoriteFolders(data);
      return NextResponse.json({ success: true });
    }

    if (action === "delete_folder") {
      if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
      data.folders = data.folders.filter((f) => f.id !== id);
      await saveFavoriteFolders(data);
      return NextResponse.json({ success: true });
    }

    return NextResponse.json({ error: "invalid action" }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// PUT — move paper to/from folder
export async function PUT(request: NextRequest) {
  try {
    const { arxivId, folderId } = (await request.json()) as {
      arxivId: string;
      folderId: string | null;
    };

    if (!arxivId) return NextResponse.json({ error: "arxivId required" }, { status: 400 });

    const data = await getFavoriteFolders();

    // Remove from all folders first
    for (const folder of data.folders) {
      const idx = folder.paperIds.indexOf(arxivId);
      if (idx >= 0) folder.paperIds.splice(idx, 1);
    }

    // Add to target folder if specified
    if (folderId) {
      const target = data.folders.find((f) => f.id === folderId);
      if (!target) return NextResponse.json({ error: "folder not found" }, { status: 404 });
      target.paperIds.push(arxivId);
    }

    await saveFavoriteFolders(data);
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// DELETE — remove from favorites
export async function DELETE(request: NextRequest) {
  try {
    const { arxivId } = (await request.json()) as { arxivId: string };
    if (!arxivId) return NextResponse.json({ error: "arxivId required" }, { status: 400 });
    await removeFavorite(arxivId);
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
