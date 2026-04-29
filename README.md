# evil-read-arxiv

> 邪修的论文阅读工作流 - 自动化论文搜索、推荐、分析和整理

## 语言 / Language

- [中文版](README.md)
- [English Version](README_en.md)

## 简介

这是一套 Claude Code 技能（Skills）集合，用于自动化研究论文的搜索、推荐、分析和整理工作流。通过调用 arXiv 和 Semantic Scholar API，每天为你推荐高质量论文，并自动生成详细笔记和关系图谱。

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-04-24 | v2.0 | 新增 Web 应用：基于 Next.js 16 的论文推荐网页端，支持 AI 智能摘要、深度分析、论文图片提取、反馈偏好学习、收藏夹管理、中英双语切换、桌面/移动端多端适配 |
| 2026-03-13 | v1.1 | 新增 `conf-papers` 技能：支持搜索 CVPR/ICCV/ECCV/ICLR/AAAI/NeurIPS/ICML 等顶级会议论文，基于 DBLP + Semantic Scholar 双数据源，独立配置文件，三维评分推荐 |
| 2026-03-01 | v1.0 | 初始版本：start-my-day 每日推荐、paper-analyze 论文分析、extract-paper-images 图片提取、paper-search 论文搜索 |

## 功能特点

### 1. start-my-day - 每日论文推荐
- 从 arXiv 搜索最近一个月的论文
- 从 Semantic Scholar 搜索过去一年的高热度论文
- 基于相关性、新近性、热门度、质量四个维度综合评分
- 自动生成今日概览和推荐列表
- 前三篇论文自动生成详细分析和提取图片
- 自动链接关键词到已有笔记

### 2. paper-analyze - 论文深度分析
- 深度分析单篇论文
- 生成结构化笔记，包含：
  - 摘要翻译和要点提炼
  - 研究背景与动机
  - 方法概述和架构
  - 实验结果分析
  - 研究价值评估
  - 优势和局限性分析
  - 与相关论文对比
- 自动提取论文图片并插入笔记
- 更新知识图谱

### 3. extract-paper-images - 论文图片提取
- 优先从 arXiv 源码包提取高质量图片
- 支持从 PDF 提取图片作为备选
- 自动生成图片索引
- 保存到笔记目录的 images 子目录

### 4. paper-search - 论文笔记搜索
- 在已有笔记中搜索论文
- 支持按标题、作者、关键词、领域搜索
- 相关性评分排序

### 5. conf-papers - 顶会论文搜索推荐
- 搜索 CVPR/ICCV/ECCV/ICLR/AAAI/NeurIPS/ICML 等顶级会议论文
- 基于 DBLP API 获取论文列表 + Semantic Scholar 补充引用和摘要
- 独立配置文件 `conf-papers.yaml`（关键词、排除词、默认年份/会议）
- 两阶段过滤：标题关键词轻量筛选 → S2 补充 → 三维评分（相关性 40% + 热门度 40% + 质量 20%）
- 前三篇论文自动生成详细分析（需有 arXiv ID）

### 6. Web 应用 - 论文推荐网页端
基于 Next.js 16 的独立 Web 应用，提供可视化论文浏览体验。详见 [web/README.zh.md](web/README.zh.md)。
- **AI 智能摘要** — 搜索论文时自动调用 Claude 批量生成摘要（主要内容 + 创新点）
- **深入了解** — 按需生成四维深度分析（核心贡献、创新点、方法概要、关键结果），并提取论文插图
- **兴趣方向搜索** — 支持两种模式：AI 语义筛选已有结果 / 重新搜索 arXiv
- **反馈与偏好学习** — 喜欢/一般/不感兴趣评价，10 条反馈后 AI 自动分析偏好并调整推荐权重
- **收藏夹** — 文件夹管理收藏论文，支持拖拽分类
- **中英双语** — UI 界面和 AI 提示词均支持中英文切换
- **多端适配** — 桌面双栏布局 + 移动端滑动卡片，支持手势导航
- **技术栈**：Next.js 16 + React 19 + TypeScript + TailwindCSS 4 + Anthropic Claude SDK

## 安装

### 前置要求

1. **Claude Code CLI** - 需要安装并配置 Claude Code（CLI 技能所需）
2. **Python 3.8+** - 用于运行搜索和分析脚本
3. **Node.js 20+** - Web 应用所需
4. **Anthropic API Key** - Web 应用的 AI 功能所需（Claude）
5. **Python 依赖**：
   ```bash
   pip install -r requirements.txt
   ```

### 安装步骤

#### 方式一：CLI 技能安装

将技能复制到 Claude Code skills 目录：

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

配置环境变量和路径（见下文"配置"部分），然后重启 Claude Code CLI。

#### 方式二：Web 应用安装

```bash
# 1. 安装 Python 依赖（项目根目录）
pip install -r requirements.txt

# 2. 安装 Node 依赖
cd web
npm install

# 3. 配置研究兴趣（项目根目录）
cd ..
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入你的研究领域和关键词

# 4. 配置 API Key（三选一，按优先级排序）
```

**API Key 配置方式：**

**方式 A：`data/api_settings.json`（推荐）**

在项目根目录创建 `data/api_settings.json`：

```json
{
  "model": "claude-sonnet-4-6",
  "api_key": "sk-ant-your-key",
  "base_url": "https://api.anthropic.com"
}
```

也可以启动应用后在设置页面（`/settings`）中直接配置。

**方式 B：环境变量**

创建 `web/.env.local`：

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
# 可选：自定义 API 地址（如代理）
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

**方式 C：直接修改源码**（不推荐在公开仓库使用）

修改 `web/src/lib/anthropic.ts` 中的 `DEFAULT_API_KEY` 和 `DEFAULT_BASE_URL` 常量。

> 优先级：`data/api_settings.json` > 环境变量 > 代码默认值

```bash
# 5. 启动 Web 应用
cd web

# 开发模式（热更新）
npm run dev

# 或 生产模式
npm run build && npm start
```

打开 http://localhost:3000 ，自动跳转到论文页面。

## CLI 技能配置

> 以下配置仅针对 CLI 技能（start-my-day、paper-analyze 等）。Web 应用的配置已在上文"Web 应用安装"中说明。
>
> **强烈建议**：先阅读 [QUICKSTART.md](QUICKSTART.md) 快速完成设置。

### 步骤1：设置环境变量（推荐）

所有脚本统一通过 `OBSIDIAN_VAULT_PATH` 环境变量读取 Obsidian Vault 路径，这是最简单的配置方式：

```bash
# Windows PowerShell（临时生效）
$env:OBSIDIAN_VAULT_PATH = "C:/Users/YourName/Documents/Obsidian Vault"

# Windows PowerShell（永久生效）
[System.Environment]::SetEnvironmentVariable("OBSIDIAN_VAULT_PATH", "C:/Users/YourName/Documents/Obsidian Vault", "User")

# macOS/Linux（添加到 ~/.bashrc 或 ~/.zshrc）
export OBSIDIAN_VAULT_PATH="/Users/yourname/Documents/Obsidian Vault"
```

设置环境变量后，**无需修改任何脚本中的路径**。

### 步骤2：创建配置文件

复制 `config.example.yaml` 并修改：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，根据你的研究兴趣修改关键词：

```yaml
vault_path: "/path/to/your/obsidian/vault"

research_domains:
  "你的研究领域1":
    keywords:
      - "keyword1"
      - "keyword2"
    arxiv_categories:
      - "cs.AI"
      - "cs.LG"
```

然后将修改后的 `config.yaml` 复制到 Vault 中：
```bash
cp config.yaml "$OBSIDIAN_VAULT_PATH/99_System/Config/research_interests.yaml"
```

### 步骤3（可选）：通过 CLI 参数覆盖路径

如果不想设置环境变量，也可以在每次调用脚本时通过参数指定路径：

```bash
python scripts/search_arxiv.py --config "/your/path/research_interests.yaml"
python scripts/scan_existing_notes.py --vault "/your/obsidian/vault"
python scripts/generate_note.py --vault "/your/obsidian/vault" --paper-id "2402.12345" --title "Paper Title" --authors "Author" --domain "大模型"
python scripts/update_graph.py --vault "/your/obsidian/vault" --paper-id "2402.12345" --title "Paper Title" --domain "大模型"
```

### 路径格式说明

- **Windows**：可以使用正斜杠 `/` 或双反斜杠 `\\`
  - 正确：`C:/Users/Name/Documents/Vault`
  - 正确：`C:\\Users\\Name\\Documents\\Vault`
  - 错误：`C:\Users\Name\Documents\Vault`（单反斜杠在 Python 字符串中需要转义）

- **macOS/Linux**：使用正斜杠 `/`
  - 正确：`/Users/name/Documents/Vault`

### Obsidian 目录结构要求

你的 Obsidian Vault 需要包含以下目录结构：

```
你的Vault/
├── 10_Daily/                    # 每日推荐笔记（自动创建）
│   └── YYYY-MM-DD论文推荐.md
├── 20_Research/
│   └── Papers/                  # 论文详细笔记目录
│       ├── 大模型/
│       │   └── 论文标题.md
│       │       └── images/      # 论文图片
│       ├── 多模态技术/
│       └── 智能体/
└── 99_System/
    └── Config/
        └── research_interests.yaml  # 研究兴趣配置（复制 config.yaml 到这里）
```

## 使用方法

### 开始每天的论文推荐

在你的 Obsidian Vault 目录下打开终端，输入：

```bash
start my day
```

这会：
1. 搜索最近一个月和过去一年的高质量论文
2. 根据你的研究兴趣筛选和评分
3. 生成今日推荐笔记（保存到 `10_Daily/` 目录）
4. 对前三篇论文自动生成详细分析
5. 提取论文图片并插入笔记
6. 自动链接关键词到已有笔记

### 分析单篇论文

如果你想深入阅读某篇论文：

```bash
paper-analyze 2602.12345
# 或使用论文标题
paper-analyze "论文标题"
```

这会：
1. 下载论文 PDF
2. 提取图片
3. 生成详细的分析笔记
4. 更新知识图谱

### 提取论文图片

```bash
extract-paper-images 2602.12345
```

### 搜索已有论文

```bash
paper-search "关键词"
```

## 目录结构

```
evil-read-arxiv/
├── README.md                 # 本文件
├── QUICKSTART.md             # 快速开始指南
├── config.example.yaml       # 配置模板（需要复制并修改）
├── requirements.txt          # Python 依赖
├── start-my-day/             # 每日推荐技能
│   ├── SKILL.md              # 技能定义文件
│   └── scripts/
│       ├── search_arxiv.py   # arXiv/Semantic Scholar 搜索脚本
│       ├── scan_existing_notes.py  # 扫描现有笔记
│       └── link_keywords.py  # 关键词自动链接脚本
├── paper-analyze/            # 论文分析技能
│   ├── SKILL.md
│   └── scripts/
│       ├── generate_note.py  # 生成笔记模板
│       └── update_graph.py   # 更新知识图谱
├── extract-paper-images/     # 图片提取技能
│   ├── SKILL.md
│   └── scripts/
│       └── extract_images.py # 图片提取脚本
├── paper-search/             # 论文搜索技能
│   └── SKILL.md
├── conf-papers/              # 顶会论文搜索推荐技能
│   ├── SKILL.md              # 技能定义文件
│   ├── conf-papers.yaml      # 独立配置（关键词、会议、年份）
│   └── scripts/
│       └── search_conf_papers.py  # DBLP搜索 + S2补充 + 评分
└── web/                      # Web 应用（Next.js 16）
    ├── README.md             # Web 英文文档
    ├── README.zh.md          # Web 中文文档
    ├── src/                  # 源码目录
    │   ├── app/              # Next.js App Router 页面和 API
    │   ├── components/       # React 组件
    │   └── lib/              # 工具库和 API 客户端
    ├── package.json
    └── next.config.ts
```

## 评分机制

论文推荐评分基于四个维度：

| 维度 | 权重 | 说明 |
|------|--------|------|
| 相关性 | 40% | 与研究兴趣的匹配程度 |
| 新近性 | 20% | 论文发布时间 |
| 热门度 | 30% | 引用数/影响力 |
| 质量 | 10% | 从摘要推断的方法质量 |

**评分细则**：
- **相关性**：标题关键词匹配（+0.5/个）、摘要关键词匹配（+0.3/个）、类别匹配（+1.0）
- **新近性**：30天内（+3）、30-90天（+2）、90-180天（+1）、180天以上（0）
- **热门度**：高影响力引用 > 100（+3）、50-100（+2）、< 50（+1）
- **质量**：多维度指标（强创新词 > 弱创新词 > 方法指标 > 量化结果 > 实验指标）

## 常用 arXiv 分类

| 分类代码 | 名称 | 说明 |
|----------|------|------|
| cs.AI | Artificial Intelligence | 人工智能 |
| cs.LG | Learning | 机器学习 |
| cs.CL | Computation and Language | 计算语言学/NLP |
| cs.CV | Computer Vision | 计算机视觉 |
| cs.MM | Multimedia | 多媒体 |
| cs.MA | Multiagent Systems | 多智能体系统 |
| cs.RO | Robotics | 机器人学 |

## 常见问题

### Q: 搜索没有结果？
A: 检查以下几点：
1. 确认网络连接正常
2. 检查配置文件中的关键词是否正确
3. 尝试扩大搜索的 arXiv 分类范围

### Q: 图片提取失败？
A:
1. 确保安装了 PyMuPDF：`pip install PyMuPDF`
2. 检查 arXiv ID 格式是否正确（如 2602.12345）

### Q: 关键词自动链接不准确？
A: 可以在 `start-my-day/scripts/link_keywords.py` 中修改 `COMMON_WORDS` 集合，添加你不需要自动链接的词

### Q: "Papers directory not found" 错误？
A:
1. 检查 `OBSIDIAN_VAULT_PATH` 环境变量是否正确设置
2. 确认 Obsidian Vault 中的目录结构是否正确创建（20_Research/Papers/）

### Q: "未指定 vault 路径" 错误？
A: 设置 `OBSIDIAN_VAULT_PATH` 环境变量，或在调用脚本时通过 `--vault` / `--config` 参数指定路径。

## 高级配置

### 修改搜索的 arXiv 分类

在调用 `search_arxiv.py` 时通过 `--categories` 参数指定：

```bash
python scripts/search_arxiv.py --categories "cs.AI,cs.LG,cs.CL,cs.CV"
```

### 修改每天推荐的论文数量

在调用 `search_arxiv.py` 时通过 `--top-n` 参数指定：

```bash
python scripts/search_arxiv.py --top-n 15
```

### 修改评分权重

在 `start-my-day/scripts/search_arxiv.py` 的 `calculate_recommendation_score` 函数中调整权重。

## 工作原理

```
用户输入 "start my day"
         ↓
    1. 加载研究配置
    2. 扫描现有笔记构建索引
         ↓
    3. 搜索 arXiv（最近30天）
    4. 搜索 Semantic Scholar（过去一年高热度）
         ↓
    5. 合并结果并去重
    6. 综合评分并排序
    7. 取前 N 篇
         ↓
    8. 生成今日推荐笔记
    9. 前三篇生成详细分析
    10. 自动链接关键词
```

## 贡献

欢迎提交 Issue 和 Pull Request！

如果你觉得这个项目对你有帮助，请给个 Star ⭐️ 支持一下！

## 许可证

MIT License

## 致谢

- [arXiv](https://arxiv.org/) - 开放获取的学术论文预印本平台
- [Semantic Scholar](https://www.semanticscholar.org/) - AI 驱动的学术研究平台
- [Claude Code](https://claude.ai/claude-code) - AI 辅助的代码和写作工具
- [Obsidian](https://obsidian.md/) - 强大的知识管理工具
