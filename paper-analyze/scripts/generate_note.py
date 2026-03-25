#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian笔记生成脚本 - 正确处理frontmatter格式
支持中英文报告生成
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def get_vault_path(cli_vault=None):
    """从CLI参数或环境变量获取vault路径"""
    if cli_vault:
        return cli_vault
    env_path = os.environ.get('OBSIDIAN_VAULT_PATH')
    if env_path:
        return env_path
    logger.error("未指定 vault 路径。请通过 --vault 参数或 OBSIDIAN_VAULT_PATH 环境变量设置。")
    sys.exit(1)


def generate_note_content(paper_id, title, authors, domain, date, language="zh"):
    """生成笔记的 Markdown 内容"""

    # 中文模板
    if language == "zh":
        domain_tags = {
            "大模型": ["大模型", "LLM"],
            "多模态技术": ["多模态", "Vision-Language"],
            "智能体": ["智能体", "Agent"],
        }
        tags = ["论文笔记"] + domain_tags.get(domain, [domain])
        tags_yaml = "\n".join(f'  - {tag}' for tag in tags)

        return f'''---
date: "{date}"
paper_id: "{paper_id}"
title: "{title}"
authors: "{authors}"
domain: "{domain}"
tags:
{tags_yaml}
quality_score: "[SCORE]/10"
related_papers: []
created: "{date}"
updated: "{date}"
status: analyzed
---

# {title}

## 核心信息
- **论文ID**：{paper_id}
- **作者**：{authors}
- **机构**：[从作者推断或查看论文]
- **发布时间**：{date}
- **会议/期刊**：[从categories推断]
- **链接**：[arXiv](https://arxiv.org/abs/{paper_id}) | [PDF](https://arxiv.org/pdf/{paper_id})
- **引用**：[如果可获取]

## 研究问题
[问题描述中文翻译和解释]

## 方法概述

### 核心方法

1. [方法1]
   - [详细描述]
   - [关键步骤]
   - [创新点]

### 数学公式（Markdown LaTeX）
- 行内公式请使用 `$...$`
- 块级公式请使用 `$$...$$` 并单独成行
- 行内示例：目标函数为 $L(\\theta)$。
- 块级示例：
    $$\\theta^* = \\arg\\min_\\theta L(\\theta)$$

### 方法架构
[架构描述和图片引用]

### 关键创新

1. [创新点1] - [为什么重要]
2. [创新点2] - [为什么重要]
3. [创新点3] - [为什么重要]

## 实验结果

### 数据集
- [数据集1]：[规模、特点]
- [数据集2]：[规模、特点]

### 实验设置
- **基线方法**：[列出对比方法]
- **评估指标**：[列出指标]
- **实验环境**：[硬件、超参数]

### 主要结果
[实验结果表格和关键发现]

## 深度分析

### 研究价值
- **理论贡献**：[理论上的贡献]
- **实际应用**：[实际应用价值]
- **领域影响**：[对研究领域的潜在影响]

### 优势
- [优势1]
- [优势2]
- [优势3]

### 局限性
- [局限1]
- [局限2]
- [局限3]

### 适用场景
- [适用场景1]
- [适用场景2]

## 与相关论文对比

### [[相关论文1]] - [对比关系]
- **差异**：[本文方法的不同之处]
- **改进**：[相比的改进点]
- **性能对比**：[如果可用]

### [[相关论文2]] - [对比关系]
[类似格式]

### [[相关论文3]] - [对比关系]
[类似格式]

## 技术路线定位

本文属于[技术路线]，主要关注[具体子方向]。

## 未来工作建议

1. [作者建议1]
2. [作者建议2]
3. [基于分析的延伸建议]

## 我的综合评价

### 价值评分
- **总体评分**：[X.X/10]
- **分项评分**：
  - 创新性：[X/10]
  - 技术质量：[X/10]
  - 实验充分性：[X/10]
  - 写作质量：[X/10]
  - 实用性：[X/10]

### 突出亮点
- [亮点1]
- [亮点2]
- [亮点3]

### 重点关注
- [需要特别关注的方面]

### 可借鉴点
- [可以学习借鉴的技术]
- [可以应用的方法]
- [有启发性的思路]

### 批判性思考
- [潜在问题]
- [可改进之处]
- [质疑点]

## 我的笔记

[用户阅读后手动补充的内容]

## 相关论文
- [[相关论文1]] - [对比关系]
- [[相关论文2]] - [对比关系]
- [[相关论文3]] - [对比关系]

## 外部资源
- [论文链接]
- [代码链接（如果有）]
- [项目主页（如果有）]
- [相关资源]
'''
    else:
        # English template
        domain_tags_en = {
            "LLM": ["LLM", "Large Language Model"],
            "Multimodal": ["Multimodal", "Vision-Language"],
            "Agent": ["Agent", "Multi-Agent"],
            "Other": ["Paper Notes"],
        }
        tags = ["paper-notes"] + domain_tags_en.get(domain, [domain])
        tags_yaml = "\n".join(f'  - {tag}' for tag in tags)

        return f'''---
date: "{date}"
paper_id: "{paper_id}"
title: "{title}"
authors: "{authors}"
domain: "{domain}"
tags:
{tags_yaml}
quality_score: "[SCORE]/10"
related_papers: []
created: "{date}"
updated: "{date}"
status: analyzed
---

# {title}

## Core Information
- **Paper ID**: {paper_id}
- **Authors**: {authors}
- **Affiliation**: [Infer from authors or check paper]
- **Publication Date**: {date}
- **Conference/Journal**: [Infer from categories]
- **Links**: [arXiv](https://arxiv.org/abs/{paper_id}) | [PDF](https://arxiv.org/pdf/{paper_id})
- **Citations**: [If available]

## Research Problem
[Problem description and explanation]

## Method Overview

### Core Method

1. [Method 1]
   - [Detailed description]
   - [Key steps]
   - [Innovation points]

### Mathematical Formula (Markdown LaTeX)
- Use `$...$` for inline formulas
- Use `$$...$$` on a separate line for block formulas
- Inline example: The objective is $L(\\theta)$.
- Block example:
    $$\\theta^* = \\arg\\min_\\theta L(\\theta)$$

### Method Architecture
[Architecture description and image references]

### Key Innovations

1. [Innovation 1] - [Why important]
2. [Innovation 2] - [Why important]
3. [Innovation 3] - [Why important]

## Experimental Results

### Datasets
- [Dataset 1]: [Scale, characteristics]
- [Dataset 2]: [Scale, characteristics]

### Experimental Settings
- **Baseline Methods**: [List comparison methods]
- **Evaluation Metrics**: [List metrics]
- **Experimental Environment**: [Hardware, hyperparameters]

### Main Results
[Experimental results table and key findings]

## Deep Analysis

### Research Value
- **Theoretical Contribution**: [Theoretical contribution]
- **Practical Applications**: [Practical application value]
- **Field Impact**: [Potential impact on research field]

### Advantages
- [Advantage 1]
- [Advantage 2]
- [Advantage 3]

### Limitations
- [Limitation 1]
- [Limitation 2]
- [Limitation 3]

### Applicable Scenarios
- [Scenario 1]
- [Scenario 2]

## Comparison with Related Papers

### [[Related Paper 1]] - [Relationship]
- **Difference**: [How this method differs]
- **Improvement**: [Improvements compared to others]
- **Performance Comparison**: [If available]

### [[Related Paper 2]] - [Relationship]
[Similar format]

### [[Related Paper 3]] - [Relationship]
[Similar format]

## Technical Track Positioning

This paper belongs to [technical track], focusing on [specific sub-direction].

## Future Work Suggestions

1. [Author's suggestion 1]
2. [Author's suggestion 2]
3. [Extension suggestions based on analysis]

## My Comprehensive Evaluation

### Value Scoring
- **Overall Score**: [X.X/10]
- **Breakdown**:
  - Innovation: [X/10]
  - Technical Quality: [X/10]
  - Experiment Thoroughness: [X/10]
  - Writing Quality: [X/10]
  - Practicality: [X/10]

### Highlights
- [Highlight 1]
- [Highlight 2]
- [Highlight 3]

### Key Points to Focus On
- [Aspects that need special attention]

### Learnings
- [Techniques to learn from]
- [Methods to apply]
- [Inspiring ideas]

### Critical Thinking
- [Potential issues]
- [Areas for improvement]
- [Points of contention]

## My Notes

[Content to be added manually after reading]

## Related Papers
- [[Related Paper 1]] - [Relationship]
- [[Related Paper 2]] - [Relationship]
- [[Related Paper 3]] - [Relationship]

## External Resources
- [Paper links]
- [Code links (if available)]
- [Project homepage (if available)]
- [Related resources]
'''


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='生成论文分析笔记 / Generate paper analysis notes')
    parser.add_argument('--paper-id', type=str, default='[PAPER_ID]', help='论文 arXiv ID / Paper arXiv ID')
    parser.add_argument('--title', type=str, default='[论文标题]', help='论文标题 / Paper title')
    parser.add_argument('--authors', type=str, default='[Authors]', help='论文作者 / Paper authors')
    parser.add_argument('--domain', type=str, default='其他', help='论文领域 / Paper domain')
    parser.add_argument('--vault', type=str, default=None, help='Obsidian vault 路径 / Obsidian vault path')
    parser.add_argument('--language', type=str, default='zh', choices=['zh', 'en'], help='语言 / Language: zh (中文) or en (English)')
    args = parser.parse_args()

    vault_root = get_vault_path(args.vault)
    papers_dir = os.path.join(vault_root, "20_Research", "Papers")
    date = datetime.now().strftime("%Y-%m-%d")

    # 清理文件名中的非法字符
    import re
    paper_title_safe = re.sub(r'[ /\\:*?"<>|]+', '_', args.title).strip('_')

    # 校验域名，防止路径穿越
    domain = args.domain.strip('/\\').replace('..', '')
    if not domain:
        domain = '其他' if args.language == 'zh' else 'Other'

    note_dir = os.path.join(papers_dir, domain)
    os.makedirs(note_dir, exist_ok=True)

    note_path = os.path.join(note_dir, f"{paper_title_safe}.md")
    content = generate_note_content(args.paper_id, args.title, args.authors, domain, date, args.language)

    try:
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        logger.error("写入笔记失败: %s", e)
        sys.exit(1)

    print(f"笔记已生成: {note_path}" if args.language == 'zh' else f"Note generated: {note_path}")
    print(f"请手动编辑笔记内容，替换占位符为实际分析结果" if args.language == 'zh' else "Please manually edit the note content, replacing placeholders with actual analysis results")


if __name__ == '__main__':
    main()
