# evil-read-arxiv Web

基于 Next.js 的 arXiv 每日论文推荐应用，集成 AI 摘要、深度分析和偏好学习。

## 功能特性

- **AI 智能摘要** — 搜索论文时自动调用 Claude 批量生成摘要（主要内容 + 创新点）
- **深入了解** — 按需生成四维深度分析（核心贡献、创新点、方法概要、关键结果）
- **兴趣方向搜索** — 支持两种模式：AI 语义筛选已有结果 / 重新搜索 arXiv
- **论文图片提取** — 自动从 arXiv 源码包提取论文插图
- **反馈与偏好学习** — 喜欢/一般/不感兴趣评价，10 条反馈后 AI 自动分析偏好并调整推荐权重
- **收藏夹** — 文件夹管理收藏论文，支持拖拽分类
- **中英双语** — UI 界面和 AI 提示词均支持中英文切换，在设置中一键切换
- **多端适配** — 桌面双栏布局 + 移动端滑动卡片

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

应用内置了默认 API，无需配置即可直接使用。如需使用自己的 API Key，有两种方式：

**方式 A：设置页面配置（推荐）**

直接启动应用，进入设置页面（`/settings`），填写 API Key 和 Base URL。配置保存在 `data/api_settings.json`。

**方式 B：环境变量配置**

创建 `web/.env.local`：

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
# 可选：自定义 API 地址（如代理）
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

优先级：设置页面 > 环境变量 > 内置默认。

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

1. **论文页** — 浏览今日推荐论文，使用搜索栏探索特定方向
2. **深入了解** — 点击论文上的「深入了解」按钮，按需生成 AI 详细分析
3. **反馈** — 对论文评价，训练你的偏好模型
4. **收藏** — 标记喜欢的论文会出现在收藏页，可用文件夹整理
5. **设置** — 切换语言（中/英）、更换 Claude 模型、管理研究领域

## 项目结构

```
web/
├── src/
│   ├── app/
│   │   ├── papers/          # 论文浏览页（搜索 + 双栏/卡片布局）
│   │   ├── favorites/       # 收藏夹（文件夹管理）
│   │   ├── settings/        # 设置页（模型、领域、语言）
│   │   └── api/
│   │       ├── papers/           # 论文搜索 + AI 批量摘要
│   │       ├── papers/filter/    # AI 语义筛选重排序
│   │       ├── papers/[id]/      # 深度分析 + 图片提取
│   │       ├── feedback/         # 用户反馈
│   │       ├── preferences/      # 偏好学习
│   │       └── settings/         # 应用设置
│   ├── components/     # React 组件（PaperCard, FeedbackButtons, NavBar 等）
│   └── lib/            # 工具库（i18n, types, data, api, python-bridge, anthropic）
├── public/
├── next.config.ts
├── package.json
└── tsconfig.json
```

## 数据目录

所有数据位于项目根目录的 `data/`（自动创建）：

| 目录 | 内容 |
|------|------|
| `papers_cache/` | 论文列表缓存及 AI 摘要（按日期 + 语言区分） |
| `analysis_cache/` | 深度分析缓存（按论文 + 语言区分） |
| `paper_images/` | 提取的论文插图 |
| `feedback.json` | 用户评价数据 |
| `api_settings.json` | API Key 和模型配置 |

## 工作原理

1. 前端通过 `python-bridge.ts` 调用 `search_arxiv.py`，按 `config.yaml` 搜索 arXiv + Semantic Scholar
2. 搜索结果由 Claude 批量生成摘要，按日期和语言缓存
3. 用户浏览论文，点击「深入了解」按需触发详细分析
4. 用户反馈定期由 Claude 分析，自动更新推荐权重
5. 语言设置同时控制 UI 文本和 Claude 提示词语言
