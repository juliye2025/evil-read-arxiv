import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import type { Paper } from "./types";

const execAsync = promisify(exec);
const PROJECT_ROOT = path.join(process.cwd(), "..");
const SCRIPT_PATH = path.join(
  PROJECT_ROOT,
  "start-my-day",
  "scripts",
  "search_arxiv.py"
);

interface ArxivScriptOutput {
  target_date: string;
  top_papers: ArxivRawPaper[];
}

interface ArxivRawPaper {
  arxiv_id: string;
  title: string;
  authors: string[];
  affiliations?: string[];
  summary?: string;
  abstract?: string;
  published?: string;
  categories?: string[];
  pdf_url?: string;
  url?: string;
  id?: string;
  source: string;
  matched_domain: string;
  matched_keywords: string[];
  scores: {
    relevance: number;
    recency: number;
    popularity: number;
    quality: number;
    recommendation: number;
  };
}

function normalizeRawPaper(raw: ArxivRawPaper): Paper {
  const arxivId =
    raw.arxiv_id || (raw.url ? raw.url.split("/abs/").pop() || "" : "");
  return {
    arxiv_id: arxivId,
    title: raw.title,
    authors: raw.authors || [],
    affiliations: raw.affiliations || [],
    summary: raw.summary || raw.abstract || "",
    original_abstract: raw.summary || raw.abstract || "",
    published_date: raw.published || "",
    categories: raw.categories || [],
    matched_domain: raw.matched_domain || "",
    matched_keywords: raw.matched_keywords || [],
    scores: raw.scores,
    pdf_url: raw.pdf_url || `https://arxiv.org/pdf/${arxivId}`,
    arxiv_url: raw.url || raw.id || `https://arxiv.org/abs/${arxivId}`,
  };
}

export async function searchPapers(
  date: string,
  configPath: string,
  topN: number = 10,
  extraArgs: string[] = [],
  days: number = 30
): Promise<Paper[]> {
  const baseArgs = [
    "python3",
    SCRIPT_PATH,
    "--config",
    configPath,
    "--output",
    "-",
    "--top-n",
    String(topN),
    "--target-date",
    date,
    "--days",
    String(days),
    ...extraArgs,
  ];

  // Quote args that contain spaces
  const cmd = baseArgs.map(a => a.includes(" ") ? `"${a}"` : a).join(" ");

  function parseOutput(stdout: string): Paper[] {
    const trimmed = stdout.trim();
    if (!trimmed) return [];
    try {
      const result: ArxivScriptOutput = JSON.parse(trimmed);
      return (result.top_papers || []).map(normalizeRawPaper);
    } catch {
      return [];
    }
  }

  try {
    const { stdout } = await execAsync(cmd, {
      cwd: path.join(PROJECT_ROOT, "start-my-day"),
      timeout: 180000,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });

    return parseOutput(stdout);
  } catch (err) {
    // Script may exit non-zero when no papers found — try parsing stdout from the error
    const execErr = err as { stdout?: string };
    if (execErr.stdout) {
      const papers = parseOutput(execErr.stdout);
      if (papers.length > 0) return papers;
    }

    // Retry with arXiv only (skip Semantic Scholar)
    console.error("Full search failed, retrying with arXiv only:", err);
    const fallbackArgs = [...baseArgs, "--skip-hot-papers"];
    const fallbackCmd = fallbackArgs.map(a => a.includes(" ") ? `"${a}"` : a).join(" ");
    try {
      const { stdout } = await execAsync(fallbackCmd, {
        cwd: path.join(PROJECT_ROOT, "start-my-day"),
        timeout: 60000,
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      });
      return parseOutput(stdout);
    } catch (fallbackErr) {
      const fbErr = fallbackErr as { stdout?: string };
      if (fbErr.stdout) {
        return parseOutput(fbErr.stdout);
      }
      return [];
    }
  }
}
