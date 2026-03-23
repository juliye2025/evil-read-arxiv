#!/usr/bin/env python3
"""
关键词链接脚本
用于 start-my-day skill，在文本中查找关键词并替换为 wikilink
"""

import re
import json
import sys
import argparse
import logging
from typing import Dict, List, Set, Tuple

from common_words import COMMON_WORDS

logger = logging.getLogger(__name__)


def parse_markdown_lines(content: str) -> List[Tuple[str, str, str, bool]]:
    """
    将 markdown 内容解析为行列表，每行包含：原始行、行类型、行内容、是否在frontmatter中

    行类型：
    - 'frontmatter': frontmatter 内容
    - 'code': 代码块
    - 'inline_code': 行内代码
    - 'wikilink': 已存在的 wikilink
    - 'image': 图片链接
    - 'link': 普通链接
    - 'heading': 标题行（以 # 开头）
    - 'normal': 普通文本

    Args:
        content: markdown 内容

    Returns:
        行列表：(原始行, 行类型, 行内容, 是否在frontmatter中)
    """
    lines = []
    in_code_block = False
    code_fence_char = None
    in_frontmatter = False
    frontmatter_count = 0

    for line in content.split('\n'):
        # 检查 frontmatter 开始/结束
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count == 1:
                in_frontmatter = True
                lines.append((line, 'frontmatter', line, True))
                continue
            elif frontmatter_count == 2:
                in_frontmatter = False
                lines.append((line, 'frontmatter', line, False))
                continue

        if in_frontmatter:
            lines.append((line, 'frontmatter', line, True))
            continue

        # 检查代码块开始/结束
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_fence_char = '```'
            else:
                in_code_block = False
                code_fence_char = None
            lines.append((line, 'code', line, False))
            continue

        if in_code_block:
            lines.append((line, 'code', line, False))
            continue

        # 解析行类型
        line_type = 'normal'
        processed_content = line

        # 检查是否是标题行
        if line.strip().startswith('#'):
            line_type = 'heading'
            lines.append((line, 'heading', line, False))
            continue

        # 检查行内代码
        inline_code_matches = list(re.finditer(r'`[^`]+`', line))
        if inline_code_matches:
            # 将行内代码替换为占位符（使用计数器，避免 pop 导致的索引错误）
            placeholders = []
            counter = [0]
            def _replace_code(m):
                idx = counter[0]
                placeholders.append(m.group(0))
                counter[0] += 1
                return f'__CODE_{idx}__'
            processed_content = re.sub(r'`[^`]+`', _replace_code, line)
            line_type = 'inline_code'

        # 检查图片（必须在 wikilink 之前，因为 ![[x]] 也包含 [[x]]）
        elif re.search(r'!\[\[.*?\]\]', line):
            line_type = 'image'

        # 检查 wikilink
        elif re.search(r'\[\[.*?\]\]', line):
            line_type = 'wikilink'

        # 检查普通链接
        elif re.search(r'\[.*?\]\(.*?\)', line):
            line_type = 'link'

        lines.append((line, line_type, processed_content, False))

    return lines


def link_keywords_in_text(
    text: str,
    keyword_index: Dict[str, List[str]],
    existing_wikilinks: Set[str]
) -> str:
    """
    在文本中链接关键词

    Args:
        text: 文本内容
        keyword_index: 关键词索引
        existing_wikilinks: 已存在的 wikilink 集合

    Returns:
        处理后的文本
    """
    # 过滤掉通用词和过短/过长的关键词
    filtered_keywords = {}
    for keyword, paths in keyword_index.items():
        keyword_lower = keyword.lower()
        # 跳过通用词
        if keyword_lower in COMMON_WORDS:
            continue
        # 跳过太短（<3字符）或太长（>30字符）的关键词
        if len(keyword) < 3 or len(keyword) > 30:
            continue
        # 跳过纯数字
        if keyword.isdigit():
            continue
        filtered_keywords[keyword] = paths

    # 按关键词长度降序排序，优先匹配更长的关键词
    sorted_keywords = sorted(
        filtered_keywords.keys(),
        key=lambda k: len(k),
        reverse=True
    )

    result = text
    matched_keywords = set()

    for keyword in sorted_keywords:
        # 跳过已匹配的关键词
        if keyword in matched_keywords:
            continue

        # 查找所有匹配（不用 \b 单词边界，支持中文环境）
        # 只匹配完整的关键词，避免匹配单词的一部分
        pattern = r'(?<![a-zA-Z0-9_-])' + re.escape(keyword) + r'(?![a-zA-Z0-9_-])'

        matches = list(re.finditer(pattern, result, re.IGNORECASE))

        if matches:
            # 获取笔记路径
            note_paths = filtered_keywords[keyword]
            if note_paths:
                # Skip keywords shared by multiple papers — they are too generic to link
                # to any specific paper (e.g. "evaluation" tagged on 50+ papers).
                if len(note_paths) > 1:
                    continue
                note_path = note_paths[0]

                # 替换所有匹配（从后往前替换，避免索引变化）
                for match in reversed(matches):
                    start, end = match.span()

                    # 检查这个匹配是否已经在 wikilink 中
                    # 查找匹配位置最近的 [[ 和 ]]
                    bracket_before = result.rfind('[[', 0, start)
                    bracket_after = result.find(']]', end)

                    # 如果存在 [[ 在前且 ]] 在后，且这个匹配在它们之间，说明已经在 wikilink 中
                    if bracket_before != -1 and bracket_after != -1 and bracket_before < start and bracket_after > end:
                        # 这个匹配已经在 wikilink 中，跳过
                        continue

                    # 使用原文中匹配到的文本，保留原始大小写
                    original_text = match.group(0)
                    wikilink = f'[[{note_path}|{original_text}]]'

                    # 替换为 wikilink
                    result = result[:start] + wikilink + result[end:]

                matched_keywords.add(keyword)

    return result


def link_keywords_in_file(
    input_file: str,
    output_file: str,
    keyword_index: Dict[str, List[str]]
) -> None:
    """
    处理输入文件并输出

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        keyword_index: 关键词索引
    """
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析为行
    lines = parse_markdown_lines(content)

    # 收集已有的 wikilink
    existing_wikilinks = set()
    for original_line, line_type, _, _ in lines:
        if line_type == 'wikilink':
            # 提取 wikilink 中的内容
            matches = re.findall(r'\[\[(.*?)\]\]', original_line)
            for match in matches:
                # 提取 wikilink 的路径部分
                parts = match.split('|')
                if parts:
                    existing_wikilinks.add(parts[0].lower())

    # 处理每行
    processed_lines = []
    for original_line, line_type, line_content, in_frontmatter in lines:
        if line_type in ['frontmatter', 'code', 'wikilink', 'image', 'link', 'heading']:
            # 不处理 frontmatter、代码块、已有 wikilink、图片、链接、标题
            processed_lines.append(original_line)
        elif line_type == 'inline_code':
            # 不替换行内代码中的内容
            processed_lines.append(original_line)
        else:
            # 处理普通文本
            processed_line = link_keywords_in_text(line_content, keyword_index, existing_wikilinks)
            processed_lines.append(processed_line)

    # 合并结果
    result = '\n'.join(processed_lines)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)

    # 统计信息
    original_links = len(re.findall(r'\[\[.*?\]\]', content))
    new_links = len(re.findall(r'\[\[.*?\]\]', result))
    added_links = new_links - original_links

    logger.info("Processed file: %s", input_file)
    logger.info("  Original wikilinks: %d", original_links)
    logger.info("  New wikilinks: %d", new_links)
    logger.info("  Added wikilinks: %d", added_links)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Link keywords to existing notes')
    parser.add_argument('--index', type=str, required=True,
                        help='Path to keyword index JSON file')
    parser.add_argument('--input', type=str, required=True,
                        help='Input file path (markdown)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output file path (markdown)')

    args = parser.parse_args()

    # 读取关键词索引
    with open(args.index, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    keyword_index = index_data.get('keyword_to_notes', {})

    # 过滤通用词
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    filtered_count = len([k for k in keyword_index if k.lower() in COMMON_WORDS])
    logger.info("Loaded index with %d keywords", len(keyword_index))
    if filtered_count > 0:
        logger.info("  Filtered %d common words", filtered_count)

    link_keywords_in_file(args.input, args.output, keyword_index)

    logger.info("Output saved to: %s", args.output)


if __name__ == '__main__':
    main()
