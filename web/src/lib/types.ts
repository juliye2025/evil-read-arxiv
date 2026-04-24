export interface Paper {
  arxiv_id: string;
  title: string;
  authors: string[];
  affiliations: string[];
  summary: string;
  original_abstract: string;
  highlights?: PaperAnalysis;
  images?: PaperImage[];
  published_date: string;
  categories: string[];
  matched_domain: string;
  matched_keywords: string[];
  scores: {
    relevance: number;
    recency: number;
    popularity: number;
    quality: number;
    recommendation: number;
  };
  pdf_url: string;
  arxiv_url: string;
  feedback?: "like" | "neutral" | "dislike";
}

export interface PaperAnalysis {
  contribution: string;
  innovation: string;
  method: string;
  results: string;
}

export interface PaperImage {
  filename: string;
  url: string;
  source: string;
}

export interface PapersResponse {
  date: string;
  papers: Paper[];
  total: number;
}

export interface FeedbackEntry {
  arxiv_id: string;
  title: string;
  rating: "like" | "neutral" | "dislike";
  date: string;
  domain: string;
  keywords: string[];
  categories: string[];
}

export interface FeedbackData {
  feedback: FeedbackEntry[];
}

export interface Preferences {
  last_updated: string | null;
  keyword_weights: Record<string, number>;
  domain_weights: Record<string, number>;
  category_weights: Record<string, number>;
  update_history: {
    date: string;
    summary: string;
    changes: Record<string, unknown>;
  }[];
}

export interface PreferenceUpdateResult {
  success: boolean;
  changes: {
    added_keywords: string[];
    removed_keywords: string[];
    priority_changes: { domain: string; old: number; new: number }[];
    summary: string;
  };
}

export interface ResearchDomain {
  keywords: string[];
  arxiv_categories: string[];
  priority: number;
}

export interface ResearchConfig {
  language: string;
  vault_path: string;
  papers_dir: string;
  research_domains: Record<string, ResearchDomain>;
  excluded_keywords: string[];
  semantic_scholar_api_key?: string;
}

export interface FavoriteFolder {
  id: string;
  name: string;
  paperIds: string[];
}

export interface FavoritesData {
  folders: FavoriteFolder[];
}

export interface AppSettings {
  claude: {
    model: string;
    api_key: string;
    max_tokens: number;
  };
  research: ResearchConfig;
  general: {
    language: string;
    daily_paper_count: number;
    obsidian_sync: boolean;
    semantic_scholar_api_key: string;
  };
}
