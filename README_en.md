# evil-read-arxiv

> Automated paper reading workflow - Search, recommend, analyze and organize research papers

## 语言 / Language

- [中文版](README.md)
- [English Version](README_en.md)

## Introduction

This is a collection of Claude Code Skills for automating research paper search, recommendation, analysis, and organization. By calling arXiv and Semantic Scholar APIs, it recommends high-quality papers daily and automatically generates detailed notes and knowledge graphs.

## Features

### 1. start-my-day - Daily Paper Recommendations
- Search papers from arXiv in the last month
- Search highly-cited papers from Semantic Scholar in the past year
- Comprehensive scoring based on relevance, recency, popularity, and quality
- Auto-generate daily overview and recommendation list
- Top 3 papers get detailed analysis and image extraction
- Auto-link keywords to existing notes

### 2. paper-analyze - Deep Paper Analysis
- Deep analysis of individual papers
- Generate structured notes including:
  - Abstract translation and key points
  - Research background and motivation
  - Method overview and architecture
  - Experimental results analysis
  - Research value assessment
  - Advantages and limitations analysis
  - Comparison with related papers
- Auto-extract paper images and insert into notes
- Update knowledge graph

### 3. extract-paper-images - Paper Image Extraction
- Prefer extracting high-quality images from arXiv source packages
- Fallback to PDF image extraction
- Auto-generate image index
- Save to notes directory's images subfolder

### 4. paper-search - Paper Note Search
- Search existing notes
- Support searching by title, author, keywords, domain
- Sort by relevance score

### 5. Web App - Paper Recommendation Web Interface
A standalone Next.js 16 web application for visual paper browsing. See [web/README.md](web/README.md) for details.
- **AI Summaries** — Auto-generated paper summaries (main content + innovations) via Claude
- **Deep Dive Analysis** — On-demand 4-section analysis (contribution, innovation, method, results) with paper figure extraction
- **Interest-based Search** — Two modes: AI semantic filtering or fresh arXiv search
- **Feedback & Preference Learning** — Like/Neutral/Not Interested ratings; AI auto-adjusts weights after 10 feedbacks
- **Favorites** — Organize liked papers into folders with drag-and-drop
- **i18n** — Chinese / English UI and AI prompts, switchable in Settings
- **Responsive** — Desktop dual-panel layout + mobile swipe cards with gesture navigation
- **Tech Stack**: Next.js 16 + React 19 + TypeScript + TailwindCSS 4 + Anthropic Claude SDK

## Installation

### Prerequisites

1. **Claude Code CLI** - Install and configure Claude Code (required for CLI skills)
2. **Python 3.8+** - For running search and analysis scripts
3. **Node.js 20+** - Required for Web app
4. **Anthropic API Key** - Required for Web app AI features (Claude)
5. **Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Installation Steps

#### Option A: CLI Skills Installation

Copy skills to your Claude Code skills directory:

```bash
# Windows PowerShell
Copy-Item -Recurse evil-read-arxiv\start-my-day $env:USERPROFILE\.claude\skills\
Copy-Item -Recurse evil-read-arxiv\paper-analyze $env:USERPROFILE\.claude\skills\
Copy-Item -Recurse evil-read-arxiv\extract-paper-images $env:USERPROFILE\.claude\skills\
Copy-Item -Recurse evil-read-arxiv\paper-search $env:USERPROFILE\.claude\skills\

# macOS/Linux
cp -r evil-read-arxiv/start-my-day ~/.claude/skills/
cp -r evil-read-arxiv/paper-analyze ~/.claude/skills/
cp -r evil-read-arxiv/extract-paper-images ~/.claude/skills/
cp -r evil-read-arxiv/paper-search ~/.claude/skills/
```

Configure environment variables and paths (see "Configuration" below), then restart Claude Code CLI.

#### Option B: Web App Installation

```bash
# 1. Install Python dependencies (project root)
pip install -r requirements.txt

# 2. Install Node dependencies
cd web
npm install

# 3. Configure research interests (project root)
cd ..
cp config.example.yaml config.yaml
# Edit config.yaml with your research domains and keywords

# 4. Configure API Key (choose one, in priority order)
```

**API Key Configuration:**

**Option A: `data/api_settings.json` (Recommended)**

Create `data/api_settings.json` at the project root:

```json
{
  "model": "claude-sonnet-4-6",
  "api_key": "sk-ant-your-key",
  "base_url": "https://api.anthropic.com"
}
```

You can also configure this via the Settings page (`/settings`) after launching the app.

**Option B: Environment Variables**

Create `web/.env.local`:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
# Optional: custom API endpoint (e.g., proxy)
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

**Option C: Edit source code directly** (not recommended for public repos)

Set `DEFAULT_API_KEY` and `DEFAULT_BASE_URL` constants in `web/src/lib/anthropic.ts`.

> Priority: `data/api_settings.json` > Environment variables > Code defaults

```bash
# 5. Start the Web app
cd web

# Development (hot reload)
npm run dev

# Or production
npm run build && npm start
```

Open http://localhost:3000 — automatically redirects to the papers page.

## CLI Skills Configuration

> The following configuration is for CLI skills only (start-my-day, paper-analyze, etc.). Web app configuration is covered in the "Web App Installation" section above.
>
> **Strongly recommended**: Read [QUICKSTART.md](QUICKSTART.md) for quick setup.

### Step 1: Set Environment Variables (Recommended)

All scripts read the Obsidian Vault path from the `OBSIDIAN_VAULT_PATH` environment variable:

```bash
# Windows PowerShell (temporary)
$env:OBSIDIAN_VAULT_PATH = "C:/Users/YourName/Documents/Obsidian Vault"

# Windows PowerShell (permanent)
[System.Environment]::SetEnvironmentVariable("OBSIDIAN_VAULT_PATH", "C:/Users/YourName/Documents/Obsidian Vault", "User")

# macOS/Linux (add to ~/.bashrc or ~/.zshrc)
export OBSIDIAN_VAULT_PATH="/Users/yourname/Documents/Obsidian Vault"
```

### Step 2: Create Config File

Copy `config.example.yaml` and modify:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`, modify keywords based on your research interests:

```yaml
# Language setting (zh/en)
language: "en"

vault_path: "/path/to/your/obsidian/vault"

research_domains:
  "LLM":
    keywords:
      - "pre-training"
      - "foundation model"
      - "large language model"
      - "LLM"
    arxiv_categories:
      - "cs.AI"
      - "cs.LG"
```

Then copy the modified `config.yaml` to your Vault:
```bash
cp config.yaml "$OBSIDIAN_VAULT_PATH/99_System/Config/research_interests.yaml"
```

### Step 3 (Optional): Override Paths via CLI Parameters

If you don't want to set environment variables, you can specify paths via parameters each time:

```bash
python scripts/search_arxiv.py --config "/your/path/research_interests.yaml"
python scripts/scan_existing_notes.py --vault "/your/obsidian/vault"
python scripts/generate_note.py --vault "/your/obsidian/vault" --paper-id "2402.12345" --title "Paper Title" --authors "Author" --domain "LLM" --language "en"
python scripts/update_graph.py --vault "/your/obsidian/vault" --paper-id "2402.12345" --title "Paper Title" --domain "LLM" --language "en"
```

### Path Format Notes

- **Windows**: Use forward slashes `/` or double backslashes `\\`
  - Correct: `C:/Users/Name/Documents/Vault`
  - Correct: `C:\\Users\\Name\\Documents\\Vault`
  - Wrong: `C:\Users\Name\Documents\Vault` (single backslash needs escaping)

- **macOS/Linux**: Use forward slashes `/`
  - Correct: `/Users/name/Documents/Vault`

### Obsidian Directory Structure Requirements

Your Obsidian Vault needs to contain:

```
yourVault/
├── 10_Daily/                    # Daily recommendation notes (auto-created)
│   └── YYYY-MM-DD-Paper-Recommendations.md
├── 20_Research/
│   └── Papers/                  # Paper detailed notes directory
│       ├── LLM/
│       │   └── Paper-Title.md
│       │       └── images/      # Paper images
│       ├── Multimodal/
│       └── Agent/
└── 99_System/
    └── Config/
        └── research_interests.yaml  # Research interests config
```

## Usage

### Start Daily Paper Recommendations

In your Obsidian Vault directory, open terminal and enter:

```bash
start my day
```

This will:
1. Search high-quality papers from the last month and past year
2. Filter and score based on your research interests
3. Generate daily recommendation notes (saved to `10_Daily/`)
4. Auto-generate detailed analysis for top 3 papers
5. Extract paper images and insert into notes
6. Auto-link keywords to existing notes

### Analyze Individual Papers

If you want to deeply read a specific paper:

```bash
paper-analyze 2602.12345
# Or use paper title
paper-analyze "Paper Title"
```

This will:
1. Download paper PDF
2. Extract images
3. Generate detailed analysis notes
4. Update knowledge graph

### Extract Paper Images

```bash
extract-paper-images 2602.12345
```

### Search Existing Papers

```bash
paper-search "keyword"
```

## Directory Structure

```
evil-read-arxiv/
├── README.md                 # Chinese version
├── README_en.md              # This file
├── QUICKSTART.md             # Quick start guide
├── config.example.yaml       # Config template
├── requirements.txt          # Python dependencies
├── start-my-day/             # Daily recommendation skill
│   ├── SKILL.md              # Skill definition
│   └── scripts/
│       ├── search_arxiv.py   # arXiv/Semantic Scholar search script
│       ├── scan_existing_notes.py  # Scan existing notes
│       └── link_keywords.py  # Auto keyword linking script
├── paper-analyze/            # Paper analysis skill
│   ├── SKILL.md
│   └── scripts/
│       ├── generate_note.py  # Generate note template
│       └── update_graph.py   # Update knowledge graph
├── extract-paper-images/      # Image extraction skill
│   ├── SKILL.md
│   └── scripts/
│       └── extract_images.py # Image extraction script
├── paper-search/             # Paper search skill
│   └── SKILL.md
├── conf-papers/              # Conference paper search skill
│   ├── SKILL.md              # Skill definition
│   ├── conf-papers.yaml      # Config (keywords, conferences, year)
│   └── scripts/
│       └── search_conf_papers.py  # DBLP search + S2 enrichment + scoring
└── web/                      # Web app (Next.js 16)
    ├── README.md             # Web English docs
    ├── README.zh.md          # Web Chinese docs
    ├── src/                  # Source code
    │   ├── app/              # Next.js App Router pages and API
    │   ├── components/       # React components
    │   └── lib/              # Utilities and API client
    ├── package.json
    └── next.config.ts
```

## Scoring Mechanism

Paper recommendation scoring based on four dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Relevance | 40% | Match with research interests |
| Recency | 20% | Paper publication time |
| Popularity | 30% | Citation count/influence |
| Quality | 10% | Method quality inferred from abstract |

**Scoring Details**:
- **Relevance**: Title keyword match (+0.5/each), abstract keyword match (+0.3/each), category match (+1.0)
- **Recency**: Within 30 days (+3), 30-90 days (+2), 90-180 days (+1), 180+ days (0)
- **Popularity**: High impact citations > 100 (+3), 50-100 (+2), < 50 (+1)
- **Quality**: Multi-dimensional indicators

## Common arXiv Categories

| Category Code | Name | Description |
|---------------|------|-------------|
| cs.AI | Artificial Intelligence | Artificial Intelligence |
| cs.LG | Learning | Machine Learning |
| cs.CL | Computation and Language | Computational Linguistics/NLP |
| cs.CV | Computer Vision | Computer Vision |
| cs.MM | Multimedia | Multimedia |
| cs.MA | Multiagent Systems | Multi-Agent Systems |
| cs.RO | Robotics | Robotics |

## FAQ

### Q: No search results?
A: Check the following:
1. Confirm network connection is normal
2. Check if keywords in config file are correct
3. Try扩大搜索的 arXiv 分类范围 (try expanding the search arXiv category range)

### Q: Image extraction failed?
A:
1. Ensure PyMuPDF is installed: `pip install PyMuPDF`
2. Check if arXiv ID format is correct (e.g., 2602.12345)

### Q: Auto keyword linking not accurate?
A: You can modify the `COMMON_WORDS` set in `start-my-day/scripts/link_keywords.py` to add words you don't want auto-linked

### Q: "Papers directory not found" error?
A:
1. Check if `OBSIDIAN_VAULT_PATH` environment variable is set correctly
2. Confirm the directory structure is correct in your Obsidian Vault (20_Research/Papers/)

### Q: "Vault path not specified" error?
A: Set `OBSIDIAN_VAULT_PATH` environment variable, or specify path via `--vault`/`--config` parameters when calling scripts.

## Advanced Configuration

### Modify Search arXiv Categories

Specify via `--categories` parameter when calling `search_arxiv.py`:

```bash
python scripts/search_arxiv.py --categories "cs.AI,cs.LG,cs.CL,cs.CV"
```

### Modify Daily Recommendation Count

Specify via `--top-n` parameter when calling `search_arxiv.py`:

```bash
python scripts/search_arxiv.py --top-n 15
```

### Modify Scoring Weights

Adjust weights in the `calculate_recommendation_score` function in `start-my-day/scripts/search_arxiv.py`.

## How It Works

```
User inputs "start my day"
         ↓
    1. Load research config
    2. Scan existing notes to build index
         ↓
    3. Search arXiv (last 30 days)
    4. Search Semantic Scholar (past year hot papers)
         ↓
    5. Merge results and deduplicate
    6. Comprehensive scoring and sorting
    7. Take top N papers
         ↓
    8. Generate daily recommendation notes
    9. Generate detailed analysis for top 3
    10. Auto-link keywords
```

## Contributing

Welcome to submit Issues and Pull Requests!

If you find this project helpful, please give a Star ⭐️!

## License

MIT License

## Acknowledgments

- [arXiv](https://arxiv.org/) - Open-access academic preprint platform
- [Semantic Scholar](https://www.semanticscholar.org/) - AI-powered academic research platform
- [Claude Code](https://claude.ai/claude-code) - AI-assisted code and writing tool
- [Obsidian](https://obsidian.md/) - Powerful knowledge management tool
