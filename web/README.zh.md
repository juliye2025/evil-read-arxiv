# evil-read-arxiv Web

基于 Next.js 的 arXiv 每日论文推荐应用，集成 AI 摘要、深度分析和偏好学习。

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | Next.js 16 (App Router) |
| 前端 | React 19, TypeScript 5 |
| 样式 | TailwindCSS 4, CSS Variables (暗色主题) |
| AI | Anthropic Claude SDK v0.90 |
| 后端桥接 | Python 子进程 (`search_arxiv.py`) |
| 数据存储 | JSON 文件 + YAML 配置（无需数据库） |

## 功能特性

- **AI 智能摘要** — 搜索论文时自动调用 Claude 批量生成摘要（主要内容 + 创新点）
- **深入了解** — 按需生成四维深度分析（核心贡献、创新点、方法概要、关键结果），并提取论文插图
- **兴趣方向搜索** — 支持两种模式：AI 语义筛选已有结果 / 重新搜索 arXiv
- **论文图片提取** — 自动从 arXiv 源码包提取论文插图，支持尺寸过滤跳过图标和 UI 碎片
- **反馈与偏好学习** — 喜欢/一般/不感兴趣评价，10 条反馈后 AI 自动分析偏好并调整推荐权重
- **收藏夹** — 文件夹管理收藏论文，支持拖拽分类
- **中英双语** — UI 界面和 AI 提示词均支持中英文切换，在设置中一键切换
- **多端适配** — 桌面双栏布局 + 移动端滑动卡片，支持手势导航

## 环境要求

- **Node.js** 20+
- **Python** 3.8+（用于 arXiv 搜索后端）
- **Anthropic API Key**（Claude）

## 快速开始

### 1. 安装依赖

```bash
# Python 依赖（在项目根目录执行）
pip install -r requirements.txt

# Node 依赖
cd web
npm install
```

### 2. 配置 API

你需要提供自己的 Anthropic API Key，有三种方式（按优先级排序）：

**方式 A：`data/api_settings.json`（推荐）**

在项目根目录创建 `data/api_settings.json`：

```json
{
  "model": "claude-sonnet-4-6",
  "api_key": "sk-ant-your-key",
  "base_url": "https://api.anthropic.com"
}
```

也可以启动应用后在设置页面（`/settings`）中配置。

**方式 B：环境变量配置**

创建 `web/.env.local`：

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
# 可选：自定义 API 地址（如代理）
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

**方式 C：直接修改 `src/lib/anthropic.ts`**

修改源码中的 `DEFAULT_API_KEY` 和 `DEFAULT_BASE_URL` 常量（不推荐在公开仓库使用）。

优先级：`data/api_settings.json` > 环境变量 > 代码默认值。

### 3. 配置研究兴趣

在项目根目录复制示例配置：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，定义你的研究领域、关键词和 arXiv 分类。应用也会根据你的搜索自动发现新领域。

### 4. 运行

```bash
cd web

# 开发模式（热更新）
npm run dev

# 生产模式
npm run build && npm start
```

打开 http://localhost:3000 ，自动跳转到 `/papers` 页面。

## 使用指南

| 页面 | 说明 |
|------|------|
| **论文页** (`/papers`) | 浏览今日推荐论文，使用搜索栏探索特定方向。桌面端：左侧列表 + 右侧详情双栏布局。移动端：滑动卡片。 |
| **深入了解** | 点击论文上的「深入了解」按钮，按需生成四维 AI 详细分析，并展示提取的论文插图。 |
| **反馈** | 对论文评价（喜欢/一般/不感兴趣），训练你的偏好模型。累计 10 条评价后 AI 自动分析偏好。 |
| **收藏** (`/favorites`) | 标记喜欢的论文会出现在收藏页，可创建文件夹、拖拽整理。 |
| **设置** (`/settings`) | 切换语言（中/英）、更换 Claude 模型、设置 API Key、管理研究领域及优先级。 |

## 项目结构

```
web/
├── src/
│   ├── app/
│   │   ├── layout.tsx               # 根布局 + Context Providers
│   │   ├── globals.css              # 暗色主题 + 动画
│   │   ├── papers/page.tsx          # 论文浏览页（搜索 + 双栏/卡片布局）
│   │   ├── favorites/page.tsx       # 收藏夹（文件夹管理）
│   │   ├── settings/page.tsx        # 设置页
│   │   └── api/
│   │       ├── papers/route.ts            # 论文搜索 + AI 批量摘要
│   │       ├── papers/filter/route.ts     # AI 语义筛选重排序
│   │       ├── papers/[id]/analyze/       # 深度分析生成
│   │       ├── papers/[id]/images/        # 论文图片提取
│   │       ├── feedback/route.ts          # 用户反馈
│   │       ├── preferences/route.ts       # 获取偏好权重
│   │       ├── preferences/update/        # 触发 AI 偏好分析
│   │       ├── favorites/route.ts         # 收藏夹及文件夹 CRUD
│   │       ├── settings/route.ts          # 应用设置读写
│   │       └── images/[...path]/route.ts  # 缓存图片服务
│   ├── components/
│   │   ├── PaperCard.tsx            # 论文详情卡片（含分析展示）
│   │   ├── PaperListItem.tsx        # 论文列表项（桌面端左侧面板）
│   │   ├── FeedbackButtons.tsx      # 喜欢/一般/不感兴趣按钮
│   │   ├── SwipeContainer.tsx       # 移动端滑动手势处理
│   │   ├── ProgressBar.tsx          # 移动端进度指示器
│   │   ├── NavBar.tsx               # 底部导航栏
│   │   ├── PapersContext.tsx        # 论文状态管理
│   │   ├── FavoritesContext.tsx     # 收藏状态管理
│   │   ├── LanguageContext.tsx      # 国际化状态管理
│   │   └── Providers.tsx            # Context Providers 包装器
│   └── lib/
│       ├── api.ts                   # 前端 API 客户端
│       ├── types.ts                 # TypeScript 类型定义
│       ├── data.ts                  # 文件读写 + 缓存工具
│       ├── anthropic.ts             # Claude 客户端初始化
│       ├── python-bridge.ts         # Python 子进程桥接
│       └── i18n.ts                  # 翻译字符串（中/英）
├── public/
├── next.config.ts
├── package.json
└── tsconfig.json
```

## 数据目录

所有数据位于项目根目录的 `data/`（自动创建）：

| 目录 / 文件 | 内容 |
|-------------|------|
| `papers_cache/` | 论文列表缓存及 AI 摘要（按日期 + 语言区分） |
| `analysis_cache/` | 深度分析缓存（按论文 + 语言区分） |
| `paper_images/` | 提取的论文插图 |
| `feedback.json` | 用户评价历史 |
| `preferences.json` | 学习到的偏好权重（关键词、领域、分类） |
| `api_settings.json` | API Key 和模型配置 |

## 工作原理

1. 前端通过 `python-bridge.ts` 调用 `search_arxiv.py`，按 `config.yaml` 搜索 arXiv + Semantic Scholar
2. 搜索结果由 Claude 批量生成摘要，按日期和语言缓存
3. 用户浏览论文，点击「深入了解」按需触发详细分析并提取论文插图
4. 用户反馈定期由 Claude 分析，自动更新 `preferences.json` 中的推荐权重
5. 语言设置同时控制 UI 文本和 Claude 提示词语言
