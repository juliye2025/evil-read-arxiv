# evil-read-arxiv Web

A Next.js web app for daily arXiv paper recommendations with AI-powered summaries, deep analysis, and preference learning.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router) |
| Frontend | React 19, TypeScript 5 |
| Styling | TailwindCSS 4, CSS Variables (dark theme) |
| AI | Anthropic Claude SDK v0.90 |
| Backend Bridge | Python subprocess (`search_arxiv.py`) |
| Data Storage | JSON files + YAML config (no database required) |

## Features

- **AI Summaries** — Auto-generated paper summaries (main content + innovations) via Claude
- **Deep Dive Analysis** — On-demand 4-section analysis (contribution, innovation, method, results) with paper figure extraction
- **Interest-based Search** — Search by topic with two modes: AI semantic filtering or fresh arXiv search
- **Paper Image Extraction** — Auto-extracts figures from arXiv source packages, with size filtering to skip icons and UI fragments
- **Feedback & Preference Learning** — Like/Neutral/Not Interested ratings; AI auto-adjusts recommendation weights after 10 feedbacks
- **Favorites** — Organize liked papers into folders with drag-and-drop
- **i18n** — Chinese / English UI and AI prompts, switchable in Settings
- **Responsive** — Desktop dual-panel layout + mobile swipe cards with gesture navigation

## Prerequisites

- **Node.js** 20+
- **Python** 3.8+ (for arXiv search backend)
- **Anthropic API Key** (Claude)

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies (from project root)
pip install -r requirements.txt

# Node dependencies
cd web
npm install
```

### 2. Configure API

You need to provide your own Anthropic API key. There are three ways (in priority order):

**Option A: `data/api_settings.json` (Recommended)**

Create `data/api_settings.json` at the project root:

```json
{
  "model": "claude-sonnet-4-6",
  "api_key": "sk-ant-your-key",
  "base_url": "https://api.anthropic.com"
}
```

You can also configure this via the Settings page (`/settings`) in the app.

**Option B: Environment Variables**

Create `web/.env.local`:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
# Optional: custom API endpoint (e.g., proxy)
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

**Option C: Edit `src/lib/anthropic.ts` directly**

Set `DEFAULT_API_KEY` and `DEFAULT_BASE_URL` constants in the source code (not recommended for public repos).

Priority: `data/api_settings.json` > Environment variables > Code defaults.

### 3. Configure Research Interests

Copy the example config at the project root:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to define your research domains, keywords, and arXiv categories. The app also auto-discovers new domains from your searches.

### 4. Run

```bash
cd web

# Development (hot reload)
npm run dev

# Production
npm run build && npm start
```

Open http://localhost:3000 — redirects to `/papers`.

## Usage

| Page | Description |
|------|-------------|
| **Papers** (`/papers`) | Browse daily recommendations. Search by topic. Desktop: dual-panel list + detail view. Mobile: swipe cards. |
| **Deep Dive** | Click the "Deep Dive" button on any paper to generate a detailed 4-section AI analysis with extracted figures. |
| **Feedback** | Rate papers (Like / Neutral / Not Interested) to train your preference model. After 10 ratings, AI auto-analyzes your preferences. |
| **Favorites** (`/favorites`) | Liked papers appear here. Create folders, drag-and-drop to organize. |
| **Settings** (`/settings`) | Switch language (zh/en), change Claude model, set API key, manage research domains and priorities. |

## Project Structure

```
web/
├── src/
│   ├── app/
│   │   ├── layout.tsx               # Root layout + context providers
│   │   ├── globals.css              # Dark theme + animations
│   │   ├── papers/page.tsx          # Paper browsing (search + dual-panel/cards)
│   │   ├── favorites/page.tsx       # Favorites with folder management
│   │   ├── settings/page.tsx        # Settings panel
│   │   └── api/
│   │       ├── papers/route.ts            # Search + batch AI summaries
│   │       ├── papers/filter/route.ts     # AI semantic re-ranking
│   │       ├── papers/[id]/analyze/       # Deep analysis generation
│   │       ├── papers/[id]/images/        # Paper figure extraction
│   │       ├── feedback/route.ts          # User ratings
│   │       ├── preferences/route.ts       # Get preference weights
│   │       ├── preferences/update/        # Trigger AI preference analysis
│   │       ├── favorites/route.ts         # Favorites & folder CRUD
│   │       ├── settings/route.ts          # App settings read/write
│   │       └── images/[...path]/route.ts  # Serve cached paper images
│   ├── components/
│   │   ├── PaperCard.tsx            # Paper detail card with analysis
│   │   ├── PaperListItem.tsx        # Paper list item (desktop left panel)
│   │   ├── FeedbackButtons.tsx      # Like / Neutral / Dislike controls
│   │   ├── SwipeContainer.tsx       # Mobile swipe gesture handler
│   │   ├── ProgressBar.tsx          # Mobile progress indicator
│   │   ├── NavBar.tsx               # Bottom navigation bar
│   │   ├── PapersContext.tsx        # Papers state management
│   │   ├── FavoritesContext.tsx     # Favorites state management
│   │   ├── LanguageContext.tsx      # i18n state management
│   │   └── Providers.tsx            # Context providers wrapper
│   └── lib/
│       ├── api.ts                   # Frontend API client
│       ├── types.ts                 # TypeScript interfaces
│       ├── data.ts                  # File I/O + caching utilities
│       ├── anthropic.ts             # Claude client initialization
│       ├── python-bridge.ts         # Python subprocess wrapper
│       └── i18n.ts                  # Translation strings (zh/en)
├── public/
├── next.config.ts
├── package.json
└── tsconfig.json
```

## Data Directories

All data lives in `data/` at the project root (auto-created):

| Directory / File | Content |
|-----------------|---------|
| `papers_cache/` | Cached paper lists with AI summaries (per date + language) |
| `analysis_cache/` | Cached deep analysis results (per paper + language) |
| `paper_images/` | Extracted paper figures |
| `feedback.json` | User ratings history |
| `preferences.json` | Learned preference weights (keywords, domains, categories) |
| `api_settings.json` | API key and model settings |

## How It Works

1. Frontend calls `search_arxiv.py` via Node child process to search arXiv + Semantic Scholar
2. Results are batch-summarized by Claude, cached per date and language
3. Users browse papers; clicking "Deep Dive" triggers on-demand detailed analysis with figure extraction
4. Feedback is collected and periodically analyzed by Claude to update recommendation weights in `preferences.json`
5. Language setting controls both UI text and Claude prompt language
