#!/usr/bin/env python3
"""
arXiv + Semantic Scholar 混合架构论文搜索脚本
用于 start-my-day skill，搜索最近一个月和最近一年的极火、极热门、极优质论文
"""

import xml.etree.ElementTree as ET
import json
import re
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)


def title_to_note_filename(title: str) -> str:
    """将论文标题转换为 Obsidian 笔记文件名（与 generate_note.py 保持一致）。

    使用与 paper-analyze/scripts/generate_note.py 完全相同的规则，
    确保 start-my-day 生成的 wikilink 路径能正确指向 paper-analyze 创建的文件。
    """
    filename = re.sub(r'[ /\\:*?"<>|]+', '_', title).strip('_')
    return filename

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logger.warning("requests library not found, using urllib for Semantic Scholar API")

# ---------------------------------------------------------------------------
# API 配置
# ---------------------------------------------------------------------------
ARXIV_NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom'
}

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_FIELDS = "title,abstract,publicationDate,citationCount,influentialCitationCount,url,authors,authors.affiliations,externalIds"

# 默认分类关键词映射（当配置中无用户自定义关键词时使用）
ARXIV_CATEGORY_KEYWORDS = {
    "cs.AI": "artificial intelligence",
    "cs.LG": "machine learning",
    "cs.CL": "computational linguistics natural language processing",
    "cs.CV": "computer vision",
    "cs.MM": "multimedia",
    "cs.MA": "multi-agent systems",
    "cs.RO": "robotics"
}

# ---------------------------------------------------------------------------
# 评分常量  —— 修改权重时只需编辑这里
# ---------------------------------------------------------------------------

# 各维度原始评分的满分值（归一化基准）
SCORE_MAX = 3.0

# 相关性评分：关键词在标题 / 摘要中匹配的加分
RELEVANCE_TITLE_KEYWORD_BOOST = 0.5
RELEVANCE_SUMMARY_KEYWORD_BOOST = 0.3
RELEVANCE_CATEGORY_MATCH_BOOST = 1.0

# 新近性阈值（天） -> 对应评分
RECENCY_THRESHOLDS = [
    (30, 3.0),
    (90, 2.0),
    (180, 1.0),
]
RECENCY_DEFAULT = 0.0

# 热门度：高影响力引用数归一化到 0-SCORE_MAX
# 含义：达到此引用数时视为满分
POPULARITY_INFLUENTIAL_CITATION_FULL_SCORE = 100

# 综合推荐评分权重（普通论文）
WEIGHTS_NORMAL = {
    'relevance': 0.40,
    'recency': 0.20,
    'popularity': 0.30,
    'quality': 0.10,
}
# 综合推荐评分权重（高影响力论文：提高热门度，降低新近性）
WEIGHTS_HOT = {
    'relevance': 0.35,
    'recency': 0.10,
    'popularity': 0.45,
    'quality': 0.10,
}

# Semantic Scholar 速率限制等待时间（秒）
S2_RATE_LIMIT_WAIT = 10
S2_CATEGORY_REQUEST_INTERVAL = 3

# Semantic Scholar API Key（可选，从配置文件读取）
S2_API_KEY = None


def load_research_config(config_path: str) -> Dict:
    """
    从 YAML 文件加载研究兴趣配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        研究配置字典
    """
    import yaml
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        # 读取 Semantic Scholar API Key（如果配置了）
        global S2_API_KEY
        S2_API_KEY = config.get('semantic_scholar_api_key')
        return config
    except Exception as e:
        logger.error("Error loading config: %s", e)
        # 返回默认配置
        return {
            "research_domains": {
                "大模型": {
                    "keywords": [
                        "pre-training", "foundation model", "model architecture",
                        "large language model", "LLM", "transformer"
                    ],
                    "arxiv_categories": ["cs.AI", "cs.LG", "cs.CL"],
                    "priority": 5
                }
            },
            "excluded_keywords": ["3D", "review", "workshop", "survey"]
        }


def calculate_date_windows(target_date: Optional[datetime] = None, days: int = 30) -> Tuple[datetime, datetime, datetime, datetime]:
    """
    计算两个时间窗口：最近N天和过去一年（除去最近N天）

    Args:
        target_date: 基准日期，如果为 None 则使用当前日期
        days: 最近搜索窗口的天数（默认30）

    Returns:
        (window_recent_start, window_recent_end, window_1y_start, window_1y_end)
    """
    if target_date is None:
        target_date = datetime.now()

    window_recent_start = target_date - timedelta(days=days)
    window_recent_end = target_date

    window_1y_start = target_date - timedelta(days=365)
    window_1y_end = target_date - timedelta(days=days + 1)

    return window_recent_start, window_recent_end, window_1y_start, window_1y_end


def search_arxiv_by_date_range(
    categories: List[str],
    start_date: datetime,
    end_date: datetime,
    max_results: int = 200,
    max_retries: int = 3
) -> List[Dict]:
    """
    使用 arXiv API 搜索指定日期范围内的论文
    
    Args:
        categories: arXiv 分类列表
        start_date: 开始日期
        end_date: 结束日期
        max_results: 最大结果数
        max_retries: 最大重试次数
        
    Returns:
        论文列表
    """
    # 构建分类查询
    category_query = "+OR+".join([f"cat:{cat}" for cat in categories])
    
    # 构建日期范围查询 (arXiv 使用 YYYYMMDD 格式)
    date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000+TO+{end_date.strftime('%Y%m%d')}2359]"
    
    # 组合查询
    full_query = f"({category_query})+AND+{date_query}"
    
    # 构建 URL
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={full_query}&"
        f"max_results={max_results}&"
        f"sortBy=submittedDate&"
        f"sortOrder=descending"
    )
    
    logger.info("[arXiv] Searching papers from %s to %s", start_date.date(), end_date.date())
    logger.debug("[arXiv] URL: %s...", url[:120])
    
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                xml_content = response.read().decode('utf-8')
                papers = parse_arxiv_xml(xml_content)
                logger.info("[arXiv] Found %d papers", len(papers))
                return papers
        except Exception as e:
            logger.warning("[arXiv] Error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                logger.info("[arXiv] Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
            else:
                logger.error("[arXiv] Failed after %d attempts", max_retries)
                return []
    
    return []


def search_arxiv_by_keywords(
    keywords: List[str],
    start_date: datetime,
    end_date: datetime,
    max_results: int = 100,
    max_retries: int = 3
) -> List[Dict]:
    """
    使用关键词直接搜索 arXiv 论文（不限分类）

    Args:
        keywords: 搜索关键词列表
        start_date: 开始日期
        end_date: 结束日期
        max_results: 最大结果数
        max_retries: 最大重试次数

    Returns:
        论文列表
    """
    # 构建关键词查询 (在 title 和 abstract 中搜索)
    keyword_parts = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        # 如果关键词包含空格，用引号包裹进行精确匹配
        if ' ' in kw:
            keyword_parts.append(f'ti:"{kw}"+OR+abs:"{kw}"')
        else:
            keyword_parts.append(f"ti:{kw}+OR+abs:{kw}")

    if not keyword_parts:
        return []

    keyword_query = "+OR+".join([f"({p})" for p in keyword_parts])

    # 构建日期范围查询
    date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000+TO+{end_date.strftime('%Y%m%d')}2359]"

    full_query = f"({keyword_query})+AND+{date_query}"

    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={urllib.parse.quote(full_query, safe='+:')}&"
        f"max_results={max_results}&"
        f"sortBy=relevance&"
        f"sortOrder=descending"
    )

    logger.info("[arXiv] Keyword search: %s", keywords)
    logger.debug("[arXiv] URL: %s...", url[:150])

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                xml_content = response.read().decode('utf-8')
                papers = parse_arxiv_xml(xml_content)
                logger.info("[arXiv] Keyword search found %d papers", len(papers))
                return papers
        except Exception as e:
            logger.warning("[arXiv] Keyword search error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                time.sleep(wait_time)
            else:
                logger.error("[arXiv] Keyword search failed after %d attempts", max_retries)
                return []

    return []


def search_semantic_scholar_hot_papers(
    query: str,
    start_date: datetime,
    end_date: datetime,
    top_k: int = 20,
    max_retries: int = 2
) -> List[Dict]:
    """
    使用 Semantic Scholar API 搜索指定时间范围内的高影响力论文

    Args:
        query: 搜索关键词
        start_date: 开始日期
        end_date: 结束日期
        top_k: 返回前 K 篇高影响力论文
        max_retries: 最大重试次数
        
    Returns:
        按高影响力引用数排序的论文列表
    """
    # 构建日期范围 (Semantic Scholar 使用 YYYY-MM-DD:YYYY-MM-DD 格式)
    date_range = f"{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"
    
    # 构建请求参数
    params = {
        "query": query,
        "publicationDateOrYear": date_range,
        "limit": 100,  # 先拉取100篇相关度最高的
        "fields": SEMANTIC_SCHOLAR_FIELDS
    }
    
    headers = {
        "User-Agent": "StartMyDay-PaperFetcher/1.0"
    }
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY
    
    logger.info("[S2] Searching hot papers from %s to %s", start_date.date(), end_date.date())
    logger.info("[S2] Query: '%s'", query)
    
    for attempt in range(max_retries):
        try:
            if HAS_REQUESTS:
                response = requests.get(
                    SEMANTIC_SCHOLAR_API_URL,
                    params=params,
                    headers=headers,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
            else:
                # 使用 urllib
                query_string = urllib.parse.urlencode(params)
                url = f"{SEMANTIC_SCHOLAR_API_URL}?{query_string}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
            
            papers = data.get("data", [])
            if not papers:
                logger.info("[S2] No papers found")
                return []
            
            # 本地二次过滤与排序
            valid_papers = []
            for p in papers:
                # 过滤掉没有标题或摘要的无效条目
                if not p.get("title") or not p.get("abstract"):
                    continue
                
                # 处理可能的 None 值
                inf_cit = p.get("influentialCitationCount") or 0
                cit = p.get("citationCount") or 0
                
                p["influentialCitationCount"] = inf_cit
                p["citationCount"] = cit
                
                # 标记来源
                p["source"] = "semantic_scholar"
                p["hot_score"] = inf_cit  # 使用高影响力引用数作为热度分数

                # 提取 affiliation 信息
                if p.get('authors') and not p.get('affiliations'):
                    affiliations = []
                    for a in p['authors']:
                        for affil in (a.get('affiliations') or []):
                            name = affil.get('name', '') if isinstance(affil, dict) else str(affil)
                            if name and name not in affiliations:
                                affiliations.append(name)
                    p['affiliations'] = affiliations
                
                valid_papers.append(p)
            
            # 按高影响力引用数倒序排列
            sorted_papers = sorted(
                valid_papers,
                key=lambda x: x["influentialCitationCount"],
                reverse=True
            )
            
            logger.info("[S2] Found %d valid papers, returning top %d", len(sorted_papers), top_k)
            return sorted_papers[:top_k]
            
        except Exception as e:
            error_msg = str(e)
            logger.warning("[S2] Error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            
            # 检查是否是 429 错误（Too Many Requests）
            is_rate_limit = False
            if HAS_REQUESTS and hasattr(e, 'response') and e.response is not None:
                is_rate_limit = e.response.status_code == 429
            else:
                is_rate_limit = "429" in error_msg or "Too Many Requests" in error_msg
            
            if attempt < max_retries - 1:
                # 对于 429 错误，使用更长的等待时间
                if is_rate_limit:
                    wait_time = S2_RATE_LIMIT_WAIT
                    logger.warning("[S2] Rate limit hit. Waiting %d seconds...", wait_time)
                else:
                    wait_time = (2 ** attempt) * 2
                    logger.info("[S2] Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
            else:
                logger.error("[S2] Failed after %d attempts", max_retries)
                return []
    
    return []


def search_hot_papers_from_categories(
    categories: List[str],
    start_date: datetime,
    end_date: datetime,
    top_k_per_category: int = 5,
    config: Optional[Dict] = None
) -> List[Dict]:
    """
    为多个 arXiv 分类搜索高影响力论文

    Args:
        categories: arXiv 分类列表
        start_date: 开始日期
        end_date: 结束日期
        top_k_per_category: 每个分类返回的论文数
        config: 研究配置（用于提取用户自定义关键词）

    Returns:
        合并后的高影响力论文列表
    """
    all_hot_papers = []
    seen_arxiv_ids = set()

    # 从配置中提取用户自定义的搜索关键词（更精准）
    user_queries = []
    if config:
        domains = config.get('research_domains', {})
        for domain_name, domain_config in domains.items():
            keywords = domain_config.get('keywords', [])
            # 取每个域的前3个关键词组合为查询
            if keywords:
                query = ' '.join(keywords[:3])
                user_queries.append(query)

    # 如果没有用户关键词，回退到分类关键词
    if not user_queries:
        user_queries = [ARXIV_CATEGORY_KEYWORDS.get(cat, cat) for cat in categories]

    # 去重查询
    seen_queries = set()
    unique_queries = []
    for q in user_queries:
        q_lower = q.lower()
        if q_lower not in seen_queries:
            seen_queries.add(q_lower)
            unique_queries.append(q)

    for query in unique_queries:

        try:
            papers = search_semantic_scholar_hot_papers(
                query=query,
                start_date=start_date,
                end_date=end_date,
                top_k=top_k_per_category
            )
        except Exception as e:
            logger.warning("[S2] Query '%s' failed: %s — skipping", query, e)
            papers = []

        # 去重（基于 arXiv ID）
        for p in papers:
            # 安全地从 externalIds 字典中提取 ArXiv 编号
            arxiv_id = p.get("externalIds", {}).get("ArXiv") if p.get("externalIds") else None
            
            # 统一写入 arxiv_id 字段，方便最后 Step 3 的全局去重
            p["arxiv_id"] = arxiv_id
            
            if arxiv_id and arxiv_id not in seen_arxiv_ids:
                seen_arxiv_ids.add(arxiv_id)
                all_hot_papers.append(p)
            elif not arxiv_id:
                # 没有 arXiv ID 的也保留（可能是其他来源的论文）
                all_hot_papers.append(p)
        
        time.sleep(S2_CATEGORY_REQUEST_INTERVAL)
    
    # 最终按影响力引用数排序
    all_hot_papers.sort(key=lambda x: x.get("influentialCitationCount", 0), reverse=True)
    
    return all_hot_papers


def parse_arxiv_xml(xml_content: str) -> List[Dict]:
    """
    解析 arXiv XML 结果
    
    Args:
        xml_content: XML 内容
        
    Returns:
        论文列表，每篇论文包含 ID、标题、作者、摘要等信息
    """
    papers = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # 查找所有 entry 元素
        for entry in root.findall('atom:entry', ARXIV_NS):
            paper = {}
            
            # 提取 ID
            id_elem = entry.find('atom:id', ARXIV_NS)
            if id_elem is not None:
                paper['id'] = id_elem.text
                # 提取 arXiv ID（从 URL 中提取）
                match = re.search(r'arXiv:(\d+\.\d+)', paper['id'])
                if match:
                    paper['arxiv_id'] = match.group(1)
                else:
                    match = re.search(r'/(\d+\.\d+)$', paper['id'])
                    if match:
                        paper['arxiv_id'] = match.group(1)
            
            # 提取标题
            title_elem = entry.find('atom:title', ARXIV_NS)
            if title_elem is not None:
                paper['title'] = title_elem.text.strip()
            
            # 提取摘要
            summary_elem = entry.find('atom:summary', ARXIV_NS)
            if summary_elem is not None:
                paper['summary'] = summary_elem.text.strip()
            
            # 提取作者（及可选的 affiliation）
            authors = []
            affiliations = []
            for author in entry.findall('atom:author', ARXIV_NS):
                name_elem = author.find('atom:name', ARXIV_NS)
                if name_elem is not None:
                    authors.append(name_elem.text)
                affil_elem = author.find('arxiv:affiliation', ARXIV_NS)
                if affil_elem is not None and affil_elem.text:
                    affil = affil_elem.text.strip()
                    if affil and affil not in affiliations:
                        affiliations.append(affil)
            paper['authors'] = authors
            paper['affiliations'] = affiliations  # 可能为空列表
            
            # 提取发布日期
            published_elem = entry.find('atom:published', ARXIV_NS)
            if published_elem is not None:
                paper['published'] = published_elem.text
                # 解析日期
                try:
                    paper['published_date'] = datetime.fromisoformat(
                        paper['published'].replace('Z', '+00:00')
                    )
                except (ValueError, TypeError):
                    paper['published_date'] = None
            
            # 提取更新日期
            updated_elem = entry.find('atom:updated', ARXIV_NS)
            if updated_elem is not None:
                paper['updated'] = updated_elem.text
            
            # 提取分类
            categories = []
            for category in entry.findall('atom:category', ARXIV_NS):
                term = category.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories
            
            # 提取 PDF 链接
            for link in entry.findall('atom:link', ARXIV_NS):
                if link.get('title') == 'pdf':
                    paper['pdf_url'] = link.get('href')
                    break
            
            # 提取主页面链接
            if 'id' in paper:
                paper['url'] = paper['id']
            
            # 标记来源
            paper['source'] = 'arxiv'
            
            papers.append(paper)
            
    except ET.ParseError as e:
        logger.error("Error parsing XML: %s", e)
        raise
    
    return papers


def calculate_relevance_score(
    paper: Dict,
    domains: Dict,
    excluded_keywords: List[str],
    focus_keywords: List[str] = None
) -> Tuple[float, Optional[str], List[str]]:
    """
    计算论文与研究兴趣的相关性评分

    当有 focus_keywords 时，以 focus 匹配为主导（高权重），
    已有兴趣域仅作为参考加分。

    Args:
        paper: 论文信息
        domains: 研究领域配置
        excluded_keywords: 排除关键词
        focus_keywords: 用户今日关注的关键词

    Returns:
        (相关性评分, 匹配的领域, 匹配的关键词列表)
    """
    focus_keywords = focus_keywords or []
    title = paper.get('title', '').lower()
    summary = paper.get('summary', '').lower() if 'summary' in paper else paper.get('abstract', '').lower()
    categories = set(paper.get('categories', []))

    # 检查排除关键词
    for keyword in excluded_keywords:
        if keyword.lower() in title or keyword.lower() in summary:
            return 0, None, []

    # ---- Focus 关键词独立评分（主导） ----
    focus_score = 0.0
    focus_matched = []
    if focus_keywords:
        for fk in focus_keywords:
            fk_lower = fk.lower().strip()
            if not fk_lower:
                continue
            if fk_lower in title:
                focus_score += 2.0  # 标题匹配：高分
                focus_matched.append(fk)
            elif fk_lower in summary:
                focus_score += 1.0  # 摘要匹配：中分
                focus_matched.append(fk)

    # ---- 已有兴趣域评分（参考） ----
    max_domain_score = 0
    best_domain = None
    domain_matched_keywords = []

    for domain_name, domain_config in domains.items():
        score = 0
        dm_keywords = []

        keywords = domain_config.get('keywords', [])
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in title:
                score += RELEVANCE_TITLE_KEYWORD_BOOST
                dm_keywords.append(keyword)
            elif keyword_lower in summary:
                score += RELEVANCE_SUMMARY_KEYWORD_BOOST
                dm_keywords.append(keyword)

        domain_categories = domain_config.get('arxiv_categories', [])
        for cat in domain_categories:
            if cat in categories:
                score += RELEVANCE_CATEGORY_MATCH_BOOST
                dm_keywords.append(cat)

        if score > max_domain_score:
            max_domain_score = score
            best_domain = domain_name
            domain_matched_keywords = dm_keywords

    # ---- 合并评分 ----
    if focus_keywords:
        # Focus 模式：focus 为主，域匹配为辅（0.3 权重）
        total_score = focus_score + max_domain_score * 0.3
        all_matched = focus_matched + [k for k in domain_matched_keywords if k not in focus_matched]
        matched_domain = best_domain if best_domain else ("搜索结果" if focus_matched else None)
    else:
        # 普通模式：纯域评分
        total_score = max_domain_score
        all_matched = domain_matched_keywords
        matched_domain = best_domain

    return total_score, matched_domain, all_matched


def calculate_recency_score(published_date: Optional[datetime]) -> float:
    """
    根据发布日期计算新近性评分
    
    Args:
        published_date: 发布日期
        
    Returns:
        新近性评分 (0-3)
    """
    if published_date is None:
        return 0
    
    now = datetime.now(published_date.tzinfo) if published_date.tzinfo else datetime.now()
    days_diff = (now - published_date).days
    
    for max_days, score in RECENCY_THRESHOLDS:
        if days_diff <= max_days:
            return score
    return RECENCY_DEFAULT


def calculate_quality_score(summary: str) -> float:
    """
    从摘要推断质量评分

    采用更细粒度的指标：强创新词权重高于弱创新词，
    量化结果和对比实验也加分。

    Args:
        summary: 论文摘要

    Returns:
        质量评分 (0-3)
    """
    if not summary:
        return 0.0
    score = 0.0
    summary_lower = summary.lower()

    strong_innovation = [
        'state-of-the-art', 'sota', 'breakthrough', 'first',
        'surpass', 'outperform', 'pioneering'
    ]
    weak_innovation = [
        'novel', 'propose', 'introduce', 'new approach',
        'new method', 'innovative'
    ]
    method_indicators = [
        'framework', 'architecture', 'algorithm', 'mechanism',
        'pipeline', 'end-to-end'
    ]
    quantitative_indicators = [
        'outperforms', 'improves by', 'achieves', 'accuracy',
        'f1', 'bleu', 'rouge', 'beats', 'surpasses'
    ]
    experiment_indicators = [
        'experiment', 'evaluation', 'benchmark', 'ablation',
        'baseline', 'comparison'
    ]

    strong_count = sum(1 for ind in strong_innovation if ind in summary_lower)
    if strong_count >= 2:
        score += 1.0
    elif strong_count == 1:
        score += 0.7
    else:
        weak_count = sum(1 for ind in weak_innovation if ind in summary_lower)
        if weak_count > 0:
            score += 0.3

    if any(ind in summary_lower for ind in method_indicators):
        score += 0.5

    if any(ind in summary_lower for ind in quantitative_indicators):
        score += 0.8
    elif any(ind in summary_lower for ind in experiment_indicators):
        score += 0.4

    return min(score, SCORE_MAX)


def calculate_recommendation_score(
    relevance_score: float,
    recency_score: float,
    popularity_score: float,
    quality_score: float,
    is_hot_paper: bool = False
) -> float:
    """
    计算综合推荐评分

    权重定义在模块顶部常量 WEIGHTS_NORMAL / WEIGHTS_HOT 中。
    对于高影响力论文（来自 Semantic Scholar），使用 WEIGHTS_HOT 提高热门度权重。

    Args:
        relevance_score: 相关性评分 (0-SCORE_MAX)
        recency_score: 新近性评分 (0-SCORE_MAX)
        popularity_score: 热门度评分 (0-SCORE_MAX)
        quality_score: 质量评分 (0-SCORE_MAX)
        is_hot_paper: 是否是高影响力论文

    Returns:
        综合推荐评分 (0-10)
    """
    scores = {
        'relevance': relevance_score,
        'recency': recency_score,
        'popularity': popularity_score,
        'quality': quality_score,
    }
    # 归一化到 0-10 分
    normalized = {k: (v / SCORE_MAX) * 10 for k, v in scores.items()}

    weights = WEIGHTS_HOT if is_hot_paper else WEIGHTS_NORMAL
    final_score = sum(normalized[k] * weights[k] for k in weights)

    return round(final_score, 2)


def filter_and_score_papers(
    papers: List[Dict],
    config: Dict,
    target_date: Optional[datetime] = None,
    is_hot_paper_batch: bool = False,
    focus_keywords: List[str] = None
) -> List[Dict]:
    """
    筛选和评分论文

    Args:
        papers: 论文列表
        config: 研究配置
        target_date: 目标日期（用于计算新近性）
        is_hot_paper_batch: 是否是高影响力论文批次

    Returns:
        筛选和评分后的论文列表
    """
    domains = config.get('research_domains', {})
    excluded_keywords = config.get('excluded_keywords', [])

    scored_papers = []

    for paper in papers:
        # 计算相关性
        relevance, matched_domain, matched_keywords = calculate_relevance_score(
            paper, domains, excluded_keywords, focus_keywords=focus_keywords or []
        )

        # 如果相关性为0，跳过
        if relevance == 0:
            continue

        # 计算新近性
        if 'published_date' in paper:
            recency = calculate_recency_score(paper.get('published_date'))
        else:
            # 对于 Semantic Scholar 的论文，使用 publicationDate
            pub_date_str = paper.get('publicationDate')
            if pub_date_str:
                pub_date = None
                for fmt in ('%Y-%m-%d', '%Y-%m', '%Y'):
                    try:
                        pub_date = datetime.strptime(pub_date_str, fmt)
                        break
                    except (ValueError, TypeError):
                        continue
                recency = calculate_recency_score(pub_date) if pub_date else 0
            else:
                recency = 0

        # 计算热门度
        if is_hot_paper_batch:
            # 高影响力论文：使用 influentialCitationCount
            inf_cit = paper.get('influentialCitationCount', 0)
            popularity = min(
                inf_cit / (POPULARITY_INFLUENTIAL_CITATION_FULL_SCORE / SCORE_MAX),
                SCORE_MAX,
            )
        else:
            # 普通论文（无引用数据）：基于新近性给一个中间热门度
            # 最近7天的新论文可能有更高的"潜在热度"
            if 'published_date' in paper and paper['published_date']:
                pub = paper['published_date']
                now = datetime.now(pub.tzinfo) if pub.tzinfo else datetime.now()
                days_old = (now - pub).days
                if days_old <= 7:
                    popularity = 2.0  # 非常新的论文有潜在热度
                elif days_old <= 14:
                    popularity = 1.5
                elif days_old <= 30:
                    popularity = 1.0
                else:
                    popularity = 0.5
            else:
                popularity = 0.5  # 无日期信息时给一个保守值

        # 计算质量
        summary = paper.get('summary', '') if 'summary' in paper else paper.get('abstract', '')
        quality = calculate_quality_score(summary)

        # 计算综合推荐评分
        recommendation_score = calculate_recommendation_score(
            relevance, recency, popularity, quality, is_hot_paper_batch
        )

        # 添加评分信息
        paper['scores'] = {
            'relevance': round(relevance, 2),
            'recency': round(recency, 2),
            'popularity': round(popularity, 2),
            'quality': round(quality, 2),
            'recommendation': recommendation_score
        }
        paper['matched_domain'] = matched_domain
        paper['matched_keywords'] = matched_keywords
        paper['is_hot_paper'] = is_hot_paper_batch

        scored_papers.append(paper)

    # 按推荐评分排序
    scored_papers.sort(key=lambda x: x['scores']['recommendation'], reverse=True)

    return scored_papers


def main():
    """主函数"""
    import argparse

    default_config = os.environ.get('OBSIDIAN_VAULT_PATH', '')
    if default_config:
        default_config = os.path.join(default_config, '99_System', 'Config', 'research_interests.yaml')

    parser = argparse.ArgumentParser(description='Search and filter arXiv papers with Semantic Scholar integration')
    parser.add_argument('--config', type=str,
                        default=default_config or None,
                        help='Path to research interests config file (or set OBSIDIAN_VAULT_PATH env var)')
    parser.add_argument('--output', type=str, default='arxiv_filtered.json',
                        help='Output JSON file path')
    parser.add_argument('--max-results', type=int, default=200,
                        help='Maximum number of results to fetch from arXiv')
    parser.add_argument('--top-n', type=int, default=10,
                        help='Number of top papers to return')
    parser.add_argument('--target-date', type=str, default=None,
                        help='Target date (YYYY-MM-DD) for filtering')
    parser.add_argument('--categories', type=str,
                        default='cs.AI,cs.LG,cs.CL,cs.CV,cs.MM,cs.MA,cs.RO',
                        help='Comma-separated list of arXiv categories')
    parser.add_argument('--skip-hot-papers', action='store_true',
                        help='Skip searching hot papers from Semantic Scholar')
    parser.add_argument('--focus', type=str, default='',
                        help='User-specified focus keywords for today (comma-separated)')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to search back (default 30)')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    focus_keywords = [k.strip() for k in args.focus.split(',') if k.strip()] if args.focus else []
    if focus_keywords:
        logger.info("Focus keywords: %s", focus_keywords)

    if not args.config:
        logger.error("未指定配置文件路径。请通过 --config 参数或 OBSIDIAN_VAULT_PATH 环境变量设置。")
        return 1

    logger.info("Loading config from: %s", args.config)
    config = load_research_config(args.config)

    # 解析目标日期
    target_date = None
    if args.target_date:
        try:
            target_date = datetime.strptime(args.target_date, '%Y-%m-%d')
            logger.info("Target date: %s", args.target_date)
        except ValueError:
            logger.error("Invalid target date format: %s", args.target_date)
            return 1
    else:
        target_date = datetime.now()
        logger.info("Using current date: %s", target_date.strftime('%Y-%m-%d'))

    window_30d_start, window_30d_end, window_1y_start, window_1y_end = calculate_date_windows(target_date, days=args.days)
    logger.info("Date windows:")
    logger.info("  Recent %d days: %s to %s", args.days, window_30d_start.date(), window_30d_end.date())
    logger.info("  Past year (31-365 days): %s to %s", window_1y_start.date(), window_1y_end.date())

    # 解析分类
    categories = args.categories.split(',')

    all_scored_papers = []
    recent_papers = []
    hot_papers = []

    if focus_keywords:
        # ========== Focus 模式：关键词搜索为主 ==========
        logger.info("=" * 70)
        logger.info("Step 1 (Focus): Keyword-based arXiv search for: %s", focus_keywords)
        logger.info("=" * 70)

        focus_papers = search_arxiv_by_keywords(
            keywords=focus_keywords,
            start_date=window_30d_start,
            end_date=window_30d_end,
            max_results=args.max_results
        )

        if focus_papers:
            scored_focus = filter_and_score_papers(
                papers=focus_papers,
                config=config,
                target_date=target_date,
                is_hot_paper_batch=False,
                focus_keywords=focus_keywords
            )
            logger.info("Scored %d focus keyword papers", len(scored_focus))
            all_scored_papers.extend(scored_focus)
        else:
            logger.warning("No papers found for focus keywords")

        # Semantic Scholar 也按 focus 搜索（补充高引用论文）
        if not args.skip_hot_papers:
            logger.info("=" * 70)
            logger.info("Step 2 (Focus): Searching hot papers for focus keywords from Semantic Scholar")
            logger.info("=" * 70)

            focus_query = " ".join(focus_keywords)
            try:
                hot_papers = search_semantic_scholar_hot_papers(
                    query=focus_query,
                    start_date=window_1y_start,
                    end_date=window_1y_end,
                    top_k=20
                )
            except Exception as e:
                logger.warning("Semantic Scholar focus search failed (non-fatal): %s", e)
                hot_papers = []

            if hot_papers:
                scored_hot = filter_and_score_papers(
                    papers=hot_papers,
                    config=config,
                    target_date=target_date,
                    is_hot_paper_batch=True,
                    focus_keywords=focus_keywords
                )
                logger.info("Scored %d hot papers for focus", len(scored_hot))
                all_scored_papers.extend(scored_hot)

    else:
        # ========== 普通模式：按兴趣域搜索 ==========
        logger.info("=" * 70)
        logger.info("Step 1: Searching recent papers (last 30 days) from arXiv")
        logger.info("=" * 70)

        recent_papers = search_arxiv_by_date_range(
            categories=categories,
            start_date=window_30d_start,
            end_date=window_30d_end,
            max_results=args.max_results
        )

        if recent_papers:
            scored_recent = filter_and_score_papers(
                papers=recent_papers,
                config=config,
                target_date=target_date,
                is_hot_paper_batch=False,
            )
            logger.info("Scored %d recent papers", len(scored_recent))
            all_scored_papers.extend(scored_recent)
        else:
            logger.warning("No recent papers found")

        # 搜索过去一年的高影响力论文（Semantic Scholar）
        if not args.skip_hot_papers:
            logger.info("=" * 70)
            logger.info("Step 2: Searching hot papers (past year) from Semantic Scholar")
            logger.info("=" * 70)

            try:
                hot_papers = search_hot_papers_from_categories(
                    categories=categories,
                    start_date=window_1y_start,
                    end_date=window_1y_end,
                    top_k_per_category=5,
                    config=config
                )
            except Exception as e:
                logger.warning("Semantic Scholar search failed (non-fatal): %s", e)
                hot_papers = []

            if hot_papers:
                scored_hot = filter_and_score_papers(
                    papers=hot_papers,
                    config=config,
                    target_date=target_date,
                    is_hot_paper_batch=True,
                )
                logger.info("Scored %d hot papers", len(scored_hot))
                all_scored_papers.extend(scored_hot)
            else:
                logger.warning("No hot papers found from Semantic Scholar")
        else:
            logger.info("Skipping hot paper search (disabled by user)")

    # ========== 第三步：合并结果并排序 ==========
    logger.info("=" * 70)
    logger.info("Step 3: Merging and ranking results")
    logger.info("=" * 70)
    
    # 按推荐评分排序
    all_scored_papers.sort(key=lambda x: x['scores']['recommendation'], reverse=True)
    
    # 去重（优先 arXiv ID，其次标题 normalize）
    seen_ids = set()
    seen_titles = set()
    unique_papers = []
    for p in all_scored_papers:
        arxiv_id = p.get('arxiv_id') or p.get('arxivId')
        if arxiv_id:
            if arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                unique_papers.append(p)
        else:
            # 没有 arXiv ID 的，使用标题去重（normalize: 小写+去标点）
            title = p.get('title', '')
            title_normalized = re.sub(r'[^a-z0-9\s]', '', title.lower()).strip()
            if title_normalized and title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_papers.append(p)
    
    logger.info("Total unique papers after deduplication: %d", len(unique_papers))

    if len(unique_papers) == 0:
        logger.warning("No papers matched the criteria!")
        return 1

    # 取前 N 篇
    top_papers = unique_papers[:args.top_n]

    # 为每篇论文补充 note_filename，与 generate_note.py 的文件名规则保持一致
    # 这样 start-my-day 生成的 wikilink 可以直接使用此字段，无需自行推断
    for paper in top_papers:
        paper['note_filename'] = title_to_note_filename(paper.get('title', ''))

    # 准备输出
    output = {
        'target_date': args.target_date or target_date.strftime('%Y-%m-%d'),
        'date_windows': {
            'recent_30d': {
                'start': window_30d_start.strftime('%Y-%m-%d'),
                'end': window_30d_end.strftime('%Y-%m-%d')
            },
            'past_year': {
                'start': window_1y_start.strftime('%Y-%m-%d'),
                'end': window_1y_end.strftime('%Y-%m-%d')
            }
        },
        'total_recent': len(recent_papers),
        'total_hot': len(hot_papers),
        'total_unique': len(unique_papers),
        'top_papers': top_papers
    }

    # 保存结果
    json_str = json.dumps(output, ensure_ascii=False, indent=2, default=str)
    if args.output == '-' or args.output == '/dev/stdout':
        sys.stdout.write(json_str)
        sys.stdout.write('\n')
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_str)
        logger.info("Results saved to: %s", args.output)
        # 同时输出到 stdout
        print(json_str)

    logger.info("Top %d papers:", len(top_papers))
    for i, p in enumerate(top_papers, 1):
        hot_marker = " [HOT]" if p.get('is_hot_paper') else ""
        logger.info("  %d. %s... (Score: %s)%s", i, p.get('title', 'N/A')[:60], p['scores']['recommendation'], hot_marker)

    return 0


if __name__ == '__main__':
    sys.exit(main())
