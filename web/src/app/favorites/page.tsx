"use client";

import { useState, useEffect, useRef } from "react";
import type { Paper, FavoriteFolder } from "@/lib/types";
import { useFavoritesContext } from "@/components/FavoritesContext";
import { useLanguage } from "@/components/LanguageContext";

function PaperItem({
  paper,
  onRemove,
  onDragStart,
  t,
}: {
  paper: Paper;
  onRemove: (id: string) => void;
  onDragStart: (e: React.DragEvent, id: string) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, paper.arxiv_id)}
      className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg p-3 hover:border-[var(--accent-blue)]/50 transition-colors cursor-grab active:cursor-grabbing group flex items-start gap-3"
    >
      <div
        className="flex-1 min-w-0 cursor-pointer"
        onClick={() => window.open(paper.arxiv_url || paper.pdf_url, "_blank")}
      >
        <h3 className="text-sm font-medium text-white group-hover:text-[var(--accent-blue)] transition-colors line-clamp-2">
          {paper.title}
        </h3>
        <div className="flex items-center gap-2 mt-1">
          {paper.matched_domain && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--accent-blue)]/15 text-[var(--accent-blue)]">
              {paper.matched_domain}
            </span>
          )}
          <span className="text-[10px] text-[var(--text-secondary)]">
            {paper.authors.slice(0, 2).join(", ")}
            {paper.authors.length > 2 ? " et al." : ""}
          </span>
          <span className="text-[10px] text-[var(--text-secondary)]">
            {paper.published_date?.slice(0, 10)}
          </span>
        </div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRemove(paper.arxiv_id);
        }}
        className="flex-shrink-0 p-1 text-[var(--text-secondary)] hover:text-[var(--accent-red)] transition-colors opacity-0 group-hover:opacity-100"
        title={t("favorites.removeFavorite")}
      >
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
        </svg>
      </button>
    </div>
  );
}

function FolderSection({
  folder,
  papers,
  expanded,
  onToggle,
  onDelete,
  onRename,
  onRemovePaper,
  onDragStart,
  onDrop,
  dragOverId,
  onDragOver,
  onDragLeave,
  t,
}: {
  folder: FavoriteFolder;
  papers: Paper[];
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  onRename: (name: string) => void;
  onRemovePaper: (id: string) => void;
  onDragStart: (e: React.DragEvent, id: string) => void;
  onDrop: (e: React.DragEvent) => void;
  dragOverId: string | null;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}) {
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState(folder.name);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const isDragOver = dragOverId === folder.id;

  return (
    <div
      className={`rounded-lg border transition-colors ${isDragOver ? "border-[var(--accent-blue)] bg-[var(--accent-blue)]/5" : "border-[var(--border)]"}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <div className="flex items-center gap-2 px-3 py-2 cursor-pointer" onClick={onToggle}>
        <span className={`text-xs transition-transform ${expanded ? "rotate-90" : ""}`}>▶</span>
        <span className="text-base">📁</span>
        {editing ? (
          <input
            ref={inputRef}
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                onRename(editName);
                setEditing(false);
              }
              if (e.key === "Escape") {
                setEditName(folder.name);
                setEditing(false);
              }
            }}
            onBlur={() => {
              onRename(editName);
              setEditing(false);
            }}
            onClick={(e) => e.stopPropagation()}
            className="flex-1 bg-transparent text-sm text-white border-b border-[var(--accent-blue)] outline-none"
          />
        ) : (
          <span className="flex-1 text-sm font-medium text-white">{folder.name}</span>
        )}
        <span className="text-xs text-[var(--text-secondary)]">{papers.length}</span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setEditing(true);
          }}
          className="p-0.5 text-[var(--text-secondary)] hover:text-[var(--accent-blue)] text-xs"
          title={t("favorites.rename")}
        >
          ✏️
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-0.5 text-[var(--text-secondary)] hover:text-[var(--accent-red)] text-xs"
          title={t("favorites.deleteFolder")}
        >
          🗑️
        </button>
      </div>
      {expanded && (
        <div className="px-3 pb-2 space-y-1.5">
          {papers.length === 0 ? (
            <p className="text-xs text-[var(--text-secondary)] py-2 text-center">
              {t("favorites.dragHint")}
            </p>
          ) : (
            papers.map((p) => (
              <PaperItem
                key={p.arxiv_id}
                paper={p}
                onRemove={onRemovePaper}
                onDragStart={onDragStart}
                t={t}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default function FavoritesPage() {
  const {
    papers,
    folders,
    loading,
    createFolder: createFolderFn,
    deleteFolder: deleteFolderFn,
    renameFolder: renameFolderFn,
    movePaper,
    removeFavorite: removeFavoriteFn,
  } = useFavoritesContext();
  const { t } = useLanguage();

  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [dragOverFolderId, setDragOverFolderId] = useState<string | null>(null);
  const [newFolderName, setNewFolderName] = useState("");
  const [showNewFolder, setShowNewFolder] = useState(false);
  const newFolderRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showNewFolder) newFolderRef.current?.focus();
  }, [showNewFolder]);

  const folderPaperIds = new Set(folders.flatMap((f) => f.paperIds));
  const uncategorized = papers.filter((p) => !folderPaperIds.has(p.arxiv_id));
  const paperMap = new Map(papers.map((p) => [p.arxiv_id, p]));

  const handleCreateFolder = async () => {
    const name = newFolderName.trim();
    if (!name) return;
    await createFolderFn(name);
    setNewFolderName("");
    setShowNewFolder(false);
  };

  const handleDragStart = (e: React.DragEvent, arxivId: string) => {
    e.dataTransfer.setData("text/plain", arxivId);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDrop = async (e: React.DragEvent, folderId: string | null) => {
    e.preventDefault();
    setDragOverFolderId(null);
    const arxivId = e.dataTransfer.getData("text/plain");
    if (!arxivId) return;
    await movePaper(arxivId, folderId);
  };

  const toggleFolder = (id: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (loading && papers.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 px-4 lg:px-6 py-3 border-b border-[var(--border)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-base lg:text-lg font-bold text-white">{t("favorites.title")}</h1>
            <span className="text-xs text-[var(--text-secondary)]">{t("favorites.count", { count: papers.length })}</span>
          </div>
          {showNewFolder ? (
            <div className="flex items-center gap-1.5">
              <input
                ref={newFolderRef}
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreateFolder();
                  if (e.key === "Escape") {
                    setShowNewFolder(false);
                    setNewFolderName("");
                  }
                }}
                placeholder={t("favorites.folderName")}
                className="px-2 py-1 rounded bg-[var(--bg-primary)] border border-[var(--border)] text-xs text-white placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)] w-28"
              />
              <button
                onClick={handleCreateFolder}
                className="px-2 py-1 rounded bg-[var(--accent-blue)] text-[var(--bg-primary)] text-xs font-bold"
              >
                {t("favorites.confirm")}
              </button>
              <button
                onClick={() => {
                  setShowNewFolder(false);
                  setNewFolderName("");
                }}
                className="px-2 py-1 rounded text-xs text-[var(--text-secondary)]"
              >
                {t("favorites.cancel")}
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowNewFolder(true)}
              className="px-3 py-1 rounded-lg bg-[var(--accent-blue)] text-[var(--bg-primary)] text-xs font-bold"
            >
              {t("favorites.newFolder")}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 lg:px-6 py-3 space-y-3 max-w-5xl mx-auto w-full">
        {papers.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 mt-16">
            <span className="text-4xl">⭐</span>
            <p className="text-sm text-[var(--text-secondary)]">{t("favorites.empty")}</p>
          </div>
        ) : (
          <>
            {folders.map((folder) => {
              const folderPapers = folder.paperIds
                .map((id) => paperMap.get(id))
                .filter((p): p is Paper => !!p);

              return (
                <FolderSection
                  key={folder.id}
                  folder={folder}
                  papers={folderPapers}
                  expanded={expandedFolders.has(folder.id)}
                  onToggle={() => toggleFolder(folder.id)}
                  onDelete={() => deleteFolderFn(folder.id)}
                  onRename={(name) => renameFolderFn(folder.id, name)}
                  onRemovePaper={removeFavoriteFn}
                  onDragStart={handleDragStart}
                  onDrop={(e) => handleDrop(e, folder.id)}
                  dragOverId={dragOverFolderId}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOverFolderId(folder.id);
                  }}
                  onDragLeave={() => setDragOverFolderId(null)}
                  t={t}
                />
              );
            })}

            <div
              className={`rounded-lg border transition-colors ${dragOverFolderId === "__uncategorized" ? "border-[var(--accent-blue)] bg-[var(--accent-blue)]/5" : "border-transparent"}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOverFolderId("__uncategorized");
              }}
              onDragLeave={() => setDragOverFolderId(null)}
              onDrop={(e) => handleDrop(e, null)}
            >
              {(uncategorized.length > 0 || folders.length > 0) && (
                <div className="flex items-center gap-2 px-1 py-1.5">
                  <span className="text-xs text-[var(--text-secondary)] font-medium">
                    {folders.length > 0 ? t("favorites.uncategorized") : t("favorites.all")}
                  </span>
                  <span className="text-xs text-[var(--text-secondary)]">{uncategorized.length}</span>
                </div>
              )}
              <div className="space-y-1.5">
                {uncategorized.map((paper) => (
                  <PaperItem
                    key={paper.arxiv_id}
                    paper={paper}
                    onRemove={removeFavoriteFn}
                    onDragStart={handleDragStart}
                    t={t}
                  />
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
