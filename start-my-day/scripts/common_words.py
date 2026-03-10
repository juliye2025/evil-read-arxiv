"""
通用词集合 —— 被 scan_existing_notes.py 和 link_keywords.py 共享。
这些词在自动提取关键词和自动链接时应被排除。

支持从配置文件加载额外的自定义过滤词。
"""

# 默认通用词集合
COMMON_WORDS = {
    # 英语功能词
    'and', 'the', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
    'to', 'as', 'or', 'but', 'not', 'a', 'an', 'is', 'are', 'was', 'were',
    'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'should', 'could', 'may', 'might', 'must',
    'can', 'need', 'use', 'using', 'via', 'through', 'over',
    'under', 'between', 'among', 'during', 'without', 'within',
    'this', 'that', 'these', 'those', 'it', 'its', 'they', 'their',
    'we', 'you', 'your', 'our', 'my', 'his', 'her',
    # 在论文标题/摘要中过于常见、缺乏区分度的ML术语
    'model', 'learning', 'training', 'data', 'system', 'method',
    'approach', 'framework', 'network', 'algorithm', 'task',
}


def load_extra_common_words(config_path=None):
    """
    从配置文件加载额外的通用词，合并到 COMMON_WORDS 中。

    Args:
        config_path: 配置文件路径（YAML）
    """
    if not config_path:
        return

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        extra_words = config.get('extra_common_words', [])
        if extra_words:
            COMMON_WORDS.update(w.lower() for w in extra_words)
    except Exception:
        pass  # 配置加载失败不影响默认行为
