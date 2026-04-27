export type Language = "zh" | "en";

const translations: Record<Language, Record<string, string>> = {
  zh: {
    // Nav
    "nav.papers": "论文",
    "nav.favorites": "收藏",
    "nav.settings": "设置",

    // Paper card sections
    "paper.coreContribution": "核心贡献",
    "paper.innovation": "创新点",
    "paper.methodSummary": "方法概要",
    "paper.keyResults": "关键结果",
    "paper.deepDive": "深入了解",
    "paper.loadingAnalysis": "正在分析...",

    // Feedback buttons
    "feedback.like": "喜欢",
    "feedback.neutral": "一般",
    "feedback.dislike": "不感兴趣",
    "feedback.viewOriginal": "原文",

    // Papers page
    "papers.today": "今天",
    "papers.thisWeek": "最近一周",
    "papers.thisMonth": "最近一个月",
    "papers.searchPlaceholder": "今天想看什么方向？例如：多模态大模型、机器人抓取...",
    "papers.searchPlaceholderCompact": "今天想看什么方向？",
    "papers.filtering": "筛选中...",
    "papers.filter": "筛选",
    "papers.filterInResults": "在当前结果中筛选",
    "papers.searching": "搜索中...",
    "papers.search": "搜索",
    "papers.searchAgain": "重新搜索",
    "papers.currentDirection": "当前方向：",
    "papers.clear": "清除",
    "papers.searchingFocus": "正在搜索「{focus}」相关论文...",
    "papers.loadingDate": "正在加载 {date} 的论文...",
    "papers.retry": "重试",
    "papers.noResultsFocus": "没有找到「{focus}」相关论文，试试其他方向？",
    "papers.noResultsDate": "{date} 暂无论文",
    "papers.updatingPrefs": "正在更新偏好...",
    "papers.updatingPrefsFromFeedback": "正在根据你的反馈更新偏好...",

    // Favorites page
    "favorites.title": "收藏夹",
    "favorites.count": "{count} 篇",
    "favorites.folderName": "文件夹名称",
    "favorites.confirm": "确定",
    "favorites.cancel": "取消",
    "favorites.newFolder": "+ 新建文件夹",
    "favorites.empty": "还没有收藏的论文，去看看今天的推荐吧",
    "favorites.dragHint": "拖拽论文到此文件夹",
    "favorites.uncategorized": "未分类",
    "favorites.all": "全部收藏",
    "favorites.removeFavorite": "取消收藏",
    "favorites.rename": "重命名",
    "favorites.deleteFolder": "删除文件夹",

    // Settings page
    "settings.claudeConfig": "Claude 模型配置",
    "settings.claudeConfigDesc": "已内置默认 API，无需配置即可使用。以下选项仅用于自定义覆盖。",
    "settings.modelSelection": "模型选择",
    "settings.apiKeyLabel": "API Key（留空使用默认）",
    "settings.apiKeyPlaceholder": "留空使用内置默认 API",
    "settings.researchInterests": "研究兴趣",
    "settings.delete": "删除",
    "settings.priority": "优先级: {value}",
    "settings.keywords": "关键词",
    "settings.arxivCategories": "arXiv 分类",
    "settings.addDomain": "+ 添加新领域",
    "settings.generalSettings": "通用设置",
    "settings.language": "语言 / Language",
    "settings.optional": "可选",
    "settings.preferenceUpdate": "偏好更新",
    "settings.triggerPreferenceAnalysis": "手动触发偏好分析",
    "settings.saving": "保存中...",
    "settings.saveSettings": "保存设置",
    "settings.newDomainPrompt": "新领域名称:",
    "settings.saved": "Settings saved!",
    "settings.failedToLoad": "Failed to load settings",
  },
  en: {
    // Nav
    "nav.papers": "Papers",
    "nav.favorites": "Favorites",
    "nav.settings": "Settings",

    // Paper card sections
    "paper.coreContribution": "Core Contribution",
    "paper.innovation": "Innovation",
    "paper.methodSummary": "Method Overview",
    "paper.keyResults": "Key Results",
    "paper.deepDive": "Deep Dive",
    "paper.loadingAnalysis": "Analyzing...",

    // Feedback buttons
    "feedback.like": "Like",
    "feedback.neutral": "OK",
    "feedback.dislike": "Not Interested",
    "feedback.viewOriginal": "Paper",

    // Papers page
    "papers.today": "Today",
    "papers.thisWeek": "This Week",
    "papers.thisMonth": "This Month",
    "papers.searchPlaceholder": "What topics interest you? e.g., multimodal LLM, robot grasping...",
    "papers.searchPlaceholderCompact": "What topics interest you?",
    "papers.filtering": "Filtering...",
    "papers.filter": "Filter",
    "papers.filterInResults": "Filter current results",
    "papers.searching": "Searching...",
    "papers.search": "Search",
    "papers.searchAgain": "Search Again",
    "papers.currentDirection": "Current topic: ",
    "papers.clear": "Clear",
    "papers.searchingFocus": "Searching for papers on \"{focus}\"...",
    "papers.loadingDate": "Loading papers for {date}...",
    "papers.retry": "Retry",
    "papers.noResultsFocus": "No papers found for \"{focus}\". Try a different topic?",
    "papers.noResultsDate": "No papers for {date}",
    "papers.updatingPrefs": "Updating preferences...",
    "papers.updatingPrefsFromFeedback": "Updating preferences based on your feedback...",

    // Favorites page
    "favorites.title": "Favorites",
    "favorites.count": "{count} papers",
    "favorites.folderName": "Folder name",
    "favorites.confirm": "OK",
    "favorites.cancel": "Cancel",
    "favorites.newFolder": "+ New Folder",
    "favorites.empty": "No favorite papers yet. Check out today's recommendations!",
    "favorites.dragHint": "Drag papers to this folder",
    "favorites.uncategorized": "Uncategorized",
    "favorites.all": "All Favorites",
    "favorites.removeFavorite": "Remove from favorites",
    "favorites.rename": "Rename",
    "favorites.deleteFolder": "Delete folder",

    // Settings page
    "settings.claudeConfig": "Claude Model Configuration",
    "settings.claudeConfigDesc": "Built-in default API is ready to use. Options below are for custom overrides only.",
    "settings.modelSelection": "Model",
    "settings.apiKeyLabel": "API Key (leave empty for default)",
    "settings.apiKeyPlaceholder": "Leave empty to use built-in default API",
    "settings.researchInterests": "Research Interests",
    "settings.delete": "Delete",
    "settings.priority": "Priority: {value}",
    "settings.keywords": "Keywords",
    "settings.arxivCategories": "arXiv Categories",
    "settings.addDomain": "+ Add New Domain",
    "settings.generalSettings": "General Settings",
    "settings.language": "Language",
    "settings.optional": "Optional",
    "settings.preferenceUpdate": "Preference Update",
    "settings.triggerPreferenceAnalysis": "Trigger Preference Analysis",
    "settings.saving": "Saving...",
    "settings.saveSettings": "Save Settings",
    "settings.newDomainPrompt": "New domain name:",
    "settings.saved": "Settings saved!",
    "settings.failedToLoad": "Failed to load settings",
  },
};

export function translate(
  lang: Language,
  key: string,
  params?: Record<string, string | number>
): string {
  const str = translations[lang]?.[key] ?? translations.zh[key] ?? key;
  if (!params) return str;
  return str.replace(/\{(\w+)\}/g, (_, k) =>
    params[k] !== undefined ? String(params[k]) : `{${k}}`
  );
}

// --- Server-side prompt templates ---

export const prompts = {
  summary: {
    zh: (title: string, abstract: string) =>
      `你是一个学术论文摘要专家。请用中文总结以下论文的主要内容和创新点。

论文标题：${title}
论文摘要：${abstract}

请严格按以下格式输出（纯文本，不要markdown）：
📌 主要内容：[2-3句话概括论文做了什么，解决了什么问题]
💡 创新点：[1-2个核心创新点]`,
    en: (title: string, abstract: string) =>
      `You are an academic paper summarization expert. Please summarize the main content and innovations of the following paper in English.

Paper title: ${title}
Paper abstract: ${abstract}

Please output in the following format (plain text, no markdown):
📌 Main content: [2-3 sentences summarizing what the paper does and what problem it solves]
💡 Innovations: [1-2 core innovations]`,
  },

  analyze: {
    zh: (title: string, abstract: string) =>
      `你是一位AI/ML领域的论文分析专家。请仔细阅读以下论文的标题和摘要，用中文生成一份结构化的深度分析。

## 论文标题
${title}

## 论文摘要
${abstract}

## 要求
请输出一个JSON对象，包含以下字段（全部用中文回答）：
{
  "contribution": "核心贡献（2-3句话，重点说明这篇论文解决了什么问题，提出了什么方法）",
  "innovation": "创新点（2-3句话，重点说明相比已有工作的新颖之处和技术突破）",
  "method": "方法概要（3-4句话，简要描述技术方案的核心思路和关键设计）",
  "results": "关键结果（2-3句话，描述主要实验结果和性能提升）"
}

只输出JSON对象，不要包含markdown代码块或其他说明。`,
    en: (title: string, abstract: string) =>
      `You are an AI/ML paper analysis expert. Please read the following paper's title and abstract carefully, and generate a structured in-depth analysis in English.

## Paper Title
${title}

## Paper Abstract
${abstract}

## Requirements
Please output a JSON object with the following fields (all in English):
{
  "contribution": "Core contribution (2-3 sentences, focus on what problem this paper solves and what method it proposes)",
  "innovation": "Innovation (2-3 sentences, focus on what's novel compared to existing work and technical breakthroughs)",
  "method": "Method overview (3-4 sentences, briefly describe the core idea and key design of the technical approach)",
  "results": "Key results (2-3 sentences, describe main experimental results and performance improvements)"
}

Only output the JSON object, no markdown code blocks or other text.`,
  },

  filter: {
    zh: (focus: string, paperList: string) =>
      `你是一位学术论文筛选专家。用户今天想看的方向是：「${focus}」

以下是今日的论文列表，每篇有编号、标题和摘要：

${paperList}

请根据用户的兴趣方向，为每篇论文打一个相关性分数（0-10），10表示高度相关。
只输出一个JSON数组，每个元素是 {"index": 编号, "score": 分数}，按分数从高到低排序。
只输出JSON，不要其他文字。`,
    en: (focus: string, paperList: string) =>
      `You are an academic paper filtering expert. The user is interested in: "${focus}"

Below is today's paper list, each with an index, title, and summary:

${paperList}

Please rate each paper's relevance to the user's interest on a scale of 0-10, where 10 means highly relevant.
Output only a JSON array, each element is {"index": number, "score": number}, sorted by score from high to low.
Output only JSON, no other text.`,
  },

  domain: {
    zh: (focus: string, sampleTitles: string) =>
      `用户搜索了新的研究方向「${focus}」，并找到了以下相关论文：
${sampleTitles}

请为这个研究方向生成一个配置，用于后续自动搜索。输出JSON：
{
  "domain_name": "简短的中文领域名（2-6个字）",
  "keywords": ["5-15个英文搜索关键词，包含该领域核心术语"],
  "arxiv_categories": ["相关的arXiv分类，如cs.AI, cs.CV等，1-5个"]
}
只输出JSON，不要其他文字。`,
    en: (focus: string, sampleTitles: string) =>
      `The user searched for a new research direction "${focus}" and found the following related papers:
${sampleTitles}

Please generate a configuration for this research direction for future automatic searches. Output JSON:
{
  "domain_name": "Short domain name (2-6 words)",
  "keywords": ["5-15 English search keywords covering core terms in this field"],
  "arxiv_categories": ["Related arXiv categories, e.g. cs.AI, cs.CV, 1-5 items"]
}
Output only JSON, no other text.`,
  },

  translateFocus: {
    zh: (focus: string) =>
      `将以下中文研究方向翻译为英文搜索关键词（用逗号分隔，3-6个关键词，只输出关键词）：
${focus}`,
    en: (focus: string) =>
      `Convert the following research topic into English search keywords (comma-separated, 3-6 keywords, output only keywords):
${focus}`,
  },
};