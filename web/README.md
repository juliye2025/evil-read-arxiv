# evil-read-arxiv Web

A Next.js web app for daily arXiv paper recommendations with AI-powered summaries, deep analysis, and preference learning.

## Features

- **AI Summaries** — Auto-generated paper summaries (main content + innovations) via Claude
- **Deep Dive Analysis** — On-demand 4-section analysis (contribution, innovation, method, results)
- **Interest-based Search** — Search by topic with two modes: AI semantic filtering or fresh arXiv search
- **Paper Image Extraction** — Auto-extracts figures from arXiv source packages
- **Feedback & Preference Learning** — Like/Neutral/Not Interested ratings; AI auto-adjusts recommendation weights after 10 feedbacks
- **Favorites** — Organize liked papers into folders with drag-and-drop
- **i18n** — Chinese / English UI and AI prompts, switchable in Settings
- **Responsive** — Desktop dual-panel + mobile swipe cards

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

The app comes with a built-in default API, so it works out of the box. To use your own API key, you have two options:

**Option A: Settings Page (Recommended)**

Just start the app and go to Settings (`/settings`). Enter your API key and base URL there. Settings are saved to `data/api_settings.json`.

**Option B: Environment Variables**

Create `web/.env.local`:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
# Optional: custom API endpoint (e.g., proxy)
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

Priority: Settings page > Environment variables > Built-in default.

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

1. **Papers page** — Browse today's recommendations. Use the search bar to explore specific topics.
2. **Deep Dive** — Click the "Deep Dive" button on a paper to generate detailed AI analysis.
3. **Feedback** — Rate papers to train your preference model.
4. **Favorites** — Liked papers appear in the Favorites tab. Organize with folders.
5. **Settings** — Switch language (zh/en), change Claude model, manage research domains.

## Project Structure

```
web/
├── src/
│   ├── app/
│   │   ├── papers/          # Paper browsing (search + dual-panel/cards)
│   │   ├── favorites/       # Favorites with folders
│   │   ├── settings/        # Settings (model, domains, language)
│   │   └── api/
│   │       ├── papers/           # Search + batch AI summaries
│   │       ├── papers/filter/    # AI semantic re-ranking
│   │       ├── papers/[id]/      # Deep analysis + image extraction
│   │       ├── feedback/         # User ratings
│   │       ├── preferences/      # Preference learning
│   │       └── settings/         # App settings API
│   ├── components/     # PaperCard, FeedbackButtons, NavBar, Contexts, etc.
│   └── lib/            # i18n, types, data, api, python-bridge, anthropic
├── public/
├── next.config.ts
├── package.json
└── tsconfig.json
```

## Data Directories

All data lives in `data/` at the project root (auto-created):

| Directory | Content |
|-----------|---------|
| `papers_cache/` | Cached paper lists with AI summaries (per date + language) |
| `analysis_cache/` | Cached deep analysis results (per paper + language) |
| `paper_images/` | Extracted paper figures |
| `feedback.json` | User ratings |
| `api_settings.json` | API key and model settings |

## How It Works

1. Frontend calls `search_arxiv.py` via Node child process to search arXiv + Semantic Scholar
2. Results are batch-summarized by Claude, cached per date and language
3. Users browse papers; clicking "Deep Dive" triggers on-demand detailed analysis
4. Feedback is collected and periodically analyzed by Claude to update recommendation weights
5. Language setting controls both UI text and Claude prompt language
