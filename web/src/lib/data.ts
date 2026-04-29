import { promises as fs } from "fs";
import path from "path";
import yaml from "js-yaml";
import type {
  FeedbackData,
  FeedbackEntry,
  Preferences,
  PapersResponse,
  Paper,
  PaperAnalysis,
  PaperImage,
  ResearchConfig,
  FavoritesData,
} from "./types";

const DATA_DIR = path.join(process.cwd(), "..", "data");
const CACHE_DIR = path.join(DATA_DIR, "papers_cache");
const ANALYSIS_CACHE_DIR = path.join(DATA_DIR, "analysis_cache");
const IMAGES_DIR = path.join(DATA_DIR, "paper_images");
const CONFIG_PATH = path.join(process.cwd(), "..", "config.yaml");

async function ensureDir(dir: string) {
  await fs.mkdir(dir, { recursive: true });
}

async function readJson<T>(filePath: string, fallback: T): Promise<T> {
  try {
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

async function writeJson(filePath: string, data: unknown) {
  await ensureDir(path.dirname(filePath));
  await fs.writeFile(filePath, JSON.stringify(data, null, 2), "utf-8");
}

// --- Feedback ---

export async function getFeedback(): Promise<FeedbackData> {
  return readJson(path.join(DATA_DIR, "feedback.json"), { feedback: [] });
}

export async function addFeedback(entry: FeedbackEntry): Promise<number> {
  const data = await getFeedback();
  const idx = data.feedback.findIndex(
    (f) => f.arxiv_id === entry.arxiv_id && f.date === entry.date
  );
  if (idx >= 0) {
    data.feedback[idx] = entry;
  } else {
    data.feedback.push(entry);
  }
  await writeJson(path.join(DATA_DIR, "feedback.json"), data);
  const prefs = await getPreferences();
  const lastUpdate = prefs.last_updated;
  const unprocessed = data.feedback.filter(
    (f) => !lastUpdate || f.date >= lastUpdate
  );
  return unprocessed.length;
}

// --- Preferences ---

export async function getPreferences(): Promise<Preferences> {
  return readJson(path.join(DATA_DIR, "preferences.json"), {
    last_updated: null,
    keyword_weights: {},
    domain_weights: {},
    category_weights: {},
    update_history: [],
  });
}

export async function savePreferences(prefs: Preferences) {
  await writeJson(path.join(DATA_DIR, "preferences.json"), prefs);
}

// --- Papers Cache ---

export async function getCachedPapers(
  date: string
): Promise<PapersResponse | null> {
  const filePath = path.join(CACHE_DIR, `${date}.json`);
  try {
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as PapersResponse;
  } catch {
    return null;
  }
}

export async function cachePapers(date: string, data: PapersResponse) {
  await ensureDir(CACHE_DIR);
  await writeJson(path.join(CACHE_DIR, `${date}.json`), data);
}

export async function listCachedDates(): Promise<string[]> {
  await ensureDir(CACHE_DIR);
  const files = await fs.readdir(CACHE_DIR);
  return files
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""))
    .sort()
    .reverse();
}

// --- Research Config (YAML) ---

export async function getResearchConfig(): Promise<ResearchConfig> {
  const raw = await fs.readFile(CONFIG_PATH, "utf-8");
  return yaml.load(raw) as ResearchConfig;
}

export async function saveResearchConfig(config: ResearchConfig) {
  const yamlStr = yaml.dump(config, { lineWidth: 120, noRefs: true });
  await fs.writeFile(CONFIG_PATH, yamlStr, "utf-8");
}

// --- Merge feedback into papers ---

export function mergeFeedback(
  papers: Paper[],
  feedback: FeedbackData
): Paper[] {
  const feedbackMap = new Map(
    feedback.feedback.map((f) => [f.arxiv_id, f.rating])
  );
  return papers.map((p) => ({
    ...p,
    feedback: feedbackMap.get(p.arxiv_id) ?? p.feedback,
  }));
}

// --- Analysis Cache ---

export async function getCachedAnalysis(
  arxivId: string
): Promise<PaperAnalysis | null> {
  const safe = arxivId.replace(/[^a-zA-Z0-9._-]/g, "_");
  const filePath = path.join(ANALYSIS_CACHE_DIR, `${safe}.json`);
  try {
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as PaperAnalysis;
  } catch {
    return null;
  }
}

export async function cacheAnalysis(
  arxivId: string,
  analysis: PaperAnalysis
) {
  const safe = arxivId.replace(/[^a-zA-Z0-9._-]/g, "_");
  await ensureDir(ANALYSIS_CACHE_DIR);
  await writeJson(path.join(ANALYSIS_CACHE_DIR, `${safe}.json`), analysis);
}

// --- Paper Images ---

export function getImagesDir(arxivId: string): string {
  const safe = arxivId.replace(/[^a-zA-Z0-9._-]/g, "_");
  return path.join(IMAGES_DIR, safe);
}

export async function getCachedImages(
  arxivId: string
): Promise<PaperImage[] | null> {
  const dir = getImagesDir(arxivId);
  const indexPath = path.join(dir, "index.json");
  try {
    const raw = await fs.readFile(indexPath, "utf-8");
    return JSON.parse(raw) as PaperImage[];
  } catch {
    return null;
  }
}

export async function cacheImages(
  arxivId: string,
  images: PaperImage[]
) {
  const dir = getImagesDir(arxivId);
  await ensureDir(dir);
  await writeJson(path.join(dir, "index.json"), images);
}

// --- Favorites (liked papers) ---

const FOLDERS_PATH = path.join(DATA_DIR, "favorites_folders.json");

export async function getFavoriteFolders(): Promise<FavoritesData> {
  return readJson(FOLDERS_PATH, { folders: [] });
}

export async function saveFavoriteFolders(data: FavoritesData) {
  await writeJson(FOLDERS_PATH, data);
}

export async function removeFavorite(arxivId: string) {
  const data = await getFeedback();
  data.feedback = data.feedback.filter(
    (f) => !(f.arxiv_id === arxivId && f.rating === "like")
  );
  await writeJson(path.join(DATA_DIR, "feedback.json"), data);

  // Also remove from any folders
  const folders = await getFavoriteFolders();
  let changed = false;
  for (const folder of folders.folders) {
    const idx = folder.paperIds.indexOf(arxivId);
    if (idx >= 0) {
      folder.paperIds.splice(idx, 1);
      changed = true;
    }
  }
  if (changed) await saveFavoriteFolders(folders);
}

export async function getFavoritePapers(): Promise<Paper[]> {
  const feedback = await getFeedback();
  const likedIds = new Set(
    feedback.feedback
      .filter((f) => f.rating === "like")
      .map((f) => f.arxiv_id)
  );

  if (likedIds.size === 0) return [];

  const dates = await listCachedDates();
  const allPapers: Paper[] = [];
  const seenIds = new Set<string>();

  for (const date of dates) {
    const cached = await getCachedPapers(date);
    if (!cached) continue;
    for (const paper of cached.papers) {
      if (likedIds.has(paper.arxiv_id) && !seenIds.has(paper.arxiv_id)) {
        seenIds.add(paper.arxiv_id);
        allPapers.push({ ...paper, feedback: "like" });
      }
    }
    if (seenIds.size >= likedIds.size) break;
  }

  return allPapers;
}
