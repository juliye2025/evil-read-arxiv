"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import type { Paper, FavoriteFolder } from "@/lib/types";
import {
  fetchFavorites as apiFetchFavorites,
  createFolder as apiCreateFolder,
  deleteFolder as apiDeleteFolder,
  renameFolder as apiRenameFolder,
  movePaperToFolder as apiMovePaper,
  removeFavorite as apiRemoveFavorite,
} from "@/lib/api";

interface FavoritesContextValue {
  papers: Paper[];
  folders: FavoriteFolder[];
  loading: boolean;
  reload: () => void;
  createFolder: (name: string) => Promise<void>;
  deleteFolder: (id: string) => Promise<void>;
  renameFolder: (id: string, name: string) => Promise<void>;
  movePaper: (arxivId: string, folderId: string | null) => Promise<void>;
  removeFavorite: (arxivId: string) => Promise<void>;
  initialized: boolean;
}

const FavoritesContext = createContext<FavoritesContextValue | null>(null);

export function useFavoritesContext() {
  const ctx = useContext(FavoritesContext);
  if (!ctx) throw new Error("useFavoritesContext must be used within FavoritesProvider");
  return ctx;
}

export function FavoritesProvider({ children }: { children: React.ReactNode }) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [folders, setFolders] = useState<FavoriteFolder[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialized, setInitialized] = useState(false);

  const reload = useCallback(() => {
    setLoading(true);
    apiFetchFavorites()
      .then(({ papers: p, folders: f }) => {
        setPapers(p);
        setFolders(f);
        setInitialized(true);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Load once on first mount
  useEffect(() => {
    if (!initialized && !loading) {
      reload();
    }
  }, [initialized, loading, reload]);

  const createFolderFn = useCallback(async (name: string) => {
    await apiCreateFolder(name);
    reload();
  }, [reload]);

  const deleteFolderFn = useCallback(async (id: string) => {
    await apiDeleteFolder(id);
    reload();
  }, [reload]);

  const renameFolderFn = useCallback(async (id: string, name: string) => {
    await apiRenameFolder(id, name);
    reload();
  }, [reload]);

  const movePaperFn = useCallback(async (arxivId: string, folderId: string | null) => {
    await apiMovePaper(arxivId, folderId);
    reload();
  }, [reload]);

  const removeFavoriteFn = useCallback(async (arxivId: string) => {
    // Optimistic update
    setPapers((prev) => prev.filter((p) => p.arxiv_id !== arxivId));
    await apiRemoveFavorite(arxivId);
    reload();
  }, [reload]);

  const value = useMemo<FavoritesContextValue>(
    () => ({
      papers,
      folders,
      loading,
      reload,
      createFolder: createFolderFn,
      deleteFolder: deleteFolderFn,
      renameFolder: renameFolderFn,
      movePaper: movePaperFn,
      removeFavorite: removeFavoriteFn,
      initialized,
    }),
    [papers, folders, loading, initialized, reload, createFolderFn, deleteFolderFn, renameFolderFn, movePaperFn, removeFavoriteFn]
  );

  return (
    <FavoritesContext.Provider value={value}>
      {children}
    </FavoritesContext.Provider>
  );
}
