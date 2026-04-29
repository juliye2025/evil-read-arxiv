import type {
  PapersResponse,
  PaperAnalysis,
  PaperImage,
  Paper,
  Preferences,
  PreferenceUpdateResult,
  AppSettings,
  FavoriteFolder,
} from "./types";

const BASE = "/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchPapers(date?: string, range?: string): Promise<PapersResponse> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  if (range) params.set("range", range);
  const qs = params.toString();
  return fetchJson(`${BASE}/papers${qs ? `?${qs}` : ""}`);
}

export async function fetchAnalysis(arxivId: string, title?: string, abstract?: string): Promise<PaperAnalysis> {
  const params = new URLSearchParams();
  if (title) params.set("title", title);
  if (abstract) params.set("abstract", abstract);
  const qs = params.toString();
  return fetchJson(`${BASE}/papers/${encodeURIComponent(arxivId)}/analyze${qs ? `?${qs}` : ""}`);
}

export async function fetchPaperImages(arxivId: string): Promise<PaperImage[]> {
  return fetchJson(`${BASE}/papers/${encodeURIComponent(arxivId)}/images`);
}

export async function fetchFavorites(): Promise<{ papers: Paper[]; folders: FavoriteFolder[] }> {
  return fetchJson(`${BASE}/favorites`);
}

export async function createFolder(name: string): Promise<{ success: boolean; folder: FavoriteFolder }> {
  return fetchJson(`${BASE}/favorites`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "create", name }),
  });
}

export async function renameFolder(id: string, name: string): Promise<{ success: boolean }> {
  return fetchJson(`${BASE}/favorites`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "rename", id, name }),
  });
}

export async function deleteFolder(id: string): Promise<{ success: boolean }> {
  return fetchJson(`${BASE}/favorites`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "delete_folder", id }),
  });
}

export async function movePaperToFolder(arxivId: string, folderId: string | null): Promise<{ success: boolean }> {
  return fetchJson(`${BASE}/favorites`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arxivId, folderId }),
  });
}

export async function removeFavorite(arxivId: string): Promise<{ success: boolean }> {
  return fetchJson(`${BASE}/favorites`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arxivId }),
  });
}

export async function submitFeedback(
  paper: Paper,
  rating: "like" | "neutral" | "dislike",
  date: string
): Promise<{ success: boolean; should_update_preferences: boolean }> {
  return fetchJson(`${BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      arxiv_id: paper.arxiv_id,
      title: paper.title,
      rating,
      date,
      domain: paper.matched_domain,
      keywords: paper.matched_keywords,
      categories: paper.categories,
    }),
  });
}

export async function fetchPreferences(): Promise<Preferences> {
  return fetchJson(`${BASE}/preferences`);
}

export async function updatePreferences(): Promise<PreferenceUpdateResult> {
  return fetchJson(`${BASE}/preferences/update`, { method: "POST" });
}

export async function fetchSettings(): Promise<AppSettings> {
  return fetchJson(`${BASE}/settings`);
}

export async function saveSettings(
  settings: Partial<AppSettings>
): Promise<{ success: boolean }> {
  return fetchJson(`${BASE}/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}

export async function fetchPapersWithFocus(
  date: string,
  focus: string,
  range?: string
): Promise<PapersResponse> {
  const params = new URLSearchParams({ date, focus });
  if (range) params.set("range", range);
  return fetchJson(`${BASE}/papers?${params.toString()}`);
}

export async function filterPapers(
  date: string,
  focus: string
): Promise<PapersResponse> {
  return fetchJson(`${BASE}/papers/filter`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ date, focus }),
  });
}
