#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 arxiv_filtered.json 为每篇推荐论文生成 ADAPT 风格的占位笔记。

- 已存在的笔记文件不会被覆盖（保护用户已填写的内容）
- frontmatter 中 status="placeholder"，等用户填完后可改为 "analyzed"
- 预填已知元信息（paper_id、作者、日期、链接、英文摘要）
- 章节保留占位文本，供用户填补
"""

import argparse
import glob
import json
import logging
import os
import re
import sys
from datetime import datetime

# Windows 默认 cp936 控制台会把脚本的 UTF-8 日志显示为乱码，统一强制 UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

logger = logging.getLogger(__name__)


DOMAIN_FOLDER_MAP = {
    "Loco-Manipulation & Whole-Body Control": "Loco-Manipulation",
    "Vision-Language-Action Models": "Foundation_Models",
    "Foundation Models & LLM Reasoning": "Foundation_Models",
    "World Models & Video Generation for Robotics": "Foundation_Models",
    "6D Rearrangement & Object Manipulation": "Robot_Manipulation",
    "Imitation Learning & Diffusion Policy": "Robot_Manipulation",
    "Reinforcement Learning for Robotics": "Robot_Manipulation",
    "Embodied AI & Navigation": "Embodied_AI",
    "3D Scene Understanding & Perception": "Embodied_AI",
    "Simulation & Benchmarks": "Embodied_AI",
}

DOMAIN_TAG_MAP = {
    "Loco-Manipulation": ["Loco-Manipulation", "WBC"],
    "Foundation_Models": ["Foundation-Models"],
    "Robot_Manipulation": ["Robot-Manipulation"],
    "Embodied_AI": ["Embodied-AI"],
    "Other": [],
}


def get_vault_path(cli_vault=None):
    if cli_vault:
        return cli_vault
    env_path = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env_path:
        return env_path
    logger.error("未指定 vault 路径。请通过 --vault 参数或 OBSIDIAN_VAULT_PATH 环境变量设置。")
    sys.exit(1)


def extract_arxiv_id(raw_id: str) -> str:
    """http://arxiv.org/abs/2604.14732v1 -> 2604.14732"""
    if not raw_id:
        return ""
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", raw_id)
    if m:
        return m.group(1)
    return raw_id.strip()


def resolve_domain_folder(matched_domain: str) -> str:
    if not matched_domain:
        return "Other"
    if matched_domain in DOMAIN_FOLDER_MAP:
        return DOMAIN_FOLDER_MAP[matched_domain]
    # fallback: sanitize
    sanitized = re.sub(r"[^\w\-]+", "_", matched_domain).strip("_")
    return sanitized or "Other"


def sanitize_filename(title: str) -> str:
    return re.sub(r'[ /\\:*?"<>|]+', "_", title).strip("_")


def format_authors(authors) -> str:
    if isinstance(authors, list):
        names = []
        for a in authors:
            if isinstance(a, dict):
                name = a.get("name") or a.get("authorId") or ""
            else:
                name = str(a or "")
            if name:
                names.append(name)
        return ", ".join(names)
    return str(authors or "")


def format_date(published_date: str) -> str:
    if not published_date:
        return datetime.now().strftime("%Y-%m-%d")
    return str(published_date)[:10]


def yaml_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace('"', '\\"')


def build_placeholder(paper: dict, today: str, note_stem: str = None) -> str:
    arxiv_id = extract_arxiv_id(paper.get("id", ""))
    title = paper.get("title", "").strip()
    authors = format_authors(paper.get("authors", []))
    published = format_date(paper.get("published_date") or paper.get("published", ""))
    categories = paper.get("categories") or []
    cat_str = ", ".join(categories) if categories else "--"
    matched_domain = paper.get("matched_domain", "")
    domain_folder = resolve_domain_folder(matched_domain)
    score = paper.get("scores", {}).get("recommendation", 0.0)
    summary = (paper.get("summary") or "").strip()
    pdf_url = paper.get("pdf_url") or f"https://arxiv.org/pdf/{arxiv_id}"
    abs_url = paper.get("url") or f"https://arxiv.org/abs/{arxiv_id}"
    if note_stem is None:
        note_stem = paper.get("note_filename") or sanitize_filename(title)

    # affiliations (may be empty)
    affiliations = paper.get("affiliations") or []
    aff_str = "; ".join(affiliations) if affiliations else "[待补充]"

    domain_tags = DOMAIN_TAG_MAP.get(domain_folder, [domain_folder])
    tags_list = ["论文笔记"] + list(domain_tags)
    tags_yaml = "\n".join(f"  - {tag}" for tag in tags_list)

    content = f'''---
date: "{published}"
paper_id: "arXiv:{arxiv_id}"
title: "{yaml_escape(title)}"
authors: "{yaml_escape(authors)}"
domain: "{domain_folder}"
matched_domain: "{yaml_escape(matched_domain)}"
tags:
{tags_yaml}
quality_score: "{score}/10"
created: "{today}"
updated: "{today}"
status: placeholder
---

# [[{note_stem}|{title}]]

> [!note] 占位笔记
> 本笔记由 `start-my-day` 自动生成。已预填论文元信息与英文摘要，其余章节请手动补充。填完后可将 frontmatter 的 `status` 从 `placeholder` 改为 `analyzed`。

## 核心信息
- **论文ID**：arXiv:{arxiv_id}
- **作者**：{authors}
- **机构**：{aff_str}
- **发布时间**：{published}
- **会议/期刊**：[待补充]
- **分类**：{cat_str}
- **推荐评分**：{score}/10（匹配领域：{matched_domain or "未分类"}）
- **链接**：[arXiv]({abs_url}) | [PDF]({pdf_url})

## 摘要翻译

### 英文摘要
{summary if summary else "[待补充]"}

### 中文翻译
[待补充]

### 核心要点提炼
- **研究背景**：[待补充]
- **研究动机**：[待补充]
- **核心方法**：[待补充]
- **主要结果**：[待补充]
- **研究意义**：[待补充]

## 研究背景与动机

### 领域现状
[待补充]

### 现有方法的局限性
[待补充]

### 研究动机
[待补充]

## 研究问题
**核心研究问题**：[待补充]

## 方法概述

### 核心思想
[待补充]

### 方法框架

#### 整体架构
<!-- 填入示例：![[2604.12345_fig1.png|800]] -->

> 图1：[待补充]

#### 各模块详细说明
[待补充]

## 实验结果

### 主要结果
| 方法 | 指标1 | 指标2 |
|------|-------|-------|
| [基线] | -- | -- |
| **本文** | -- | -- |

### 消融实验
[待补充]

## 深度分析

### 研究价值评估

#### 理论贡献
[待补充]

#### 实际应用价值
[待补充]

### 局限性分析
1. [待补充]
2. [待补充]

## 未来工作建议

### 作者建议
1. [待补充]

### 基于分析的方向
1. [待补充]

## 我的综合评价

### 价值评分：**[X.X]/10**

| 评分维度 | 分数 | 理由 |
|----------|------|------|
| 创新性 | [X]/10 | [待补充] |
| 技术质量 | [X]/10 | [待补充] |
| 实验充分性 | [X]/10 | [待补充] |
| 写作质量 | [X]/10 | [待补充] |
| 实用性 | [X]/10 | [待补充] |

### 与本研究方向的相关性
[待补充 — 与 Loco-Manipulation + 大模型 WBC 方向的关联]

## 相关论文

### 直接相关
<!-- 例：- [[Paper_Stem|论文标题]] - 关系描述 -->

### 背景相关
<!-- 例：- [[Paper_Stem|论文标题]] - 关系描述 -->

> [!tip] 关键启示
> [待补充]

> [!warning] 注意事项
> [待补充]

> [!success] 推荐指数
> [⭐ 数量 + 简短评语]
'''
    return content


def build_existing_stems(vault_root: str):
    """扫描 20_Research/Papers/ 下所有 .md 的文件名 stem（小写），用于跨文件夹查重。"""
    papers_dir = os.path.join(vault_root, "20_Research", "Papers")
    stems = {}
    if not os.path.isdir(papers_dir):
        return stems
    for path in glob.glob(os.path.join(papers_dir, "**", "*.md"), recursive=True):
        stem = os.path.splitext(os.path.basename(path))[0].lower()
        stems.setdefault(stem, path)
    return stems


def _read_fm_paper_id(path: str) -> str:
    """从已存在 .md 的 frontmatter 读 paper_id，用于短名冲突判定。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(3000)
    except (IOError, OSError, UnicodeDecodeError):
        return ""
    m = re.search(r'^paper_id:\s*["\']?([^"\'\n]+?)["\']?\s*$', head, re.M)
    if not m:
        return ""
    return re.sub(r'^arXiv:', '', m.group(1).strip(), flags=re.I)


def write_placeholder(vault_root: str, paper: dict, today: str, existing_stems: dict, dry_run: bool = False):
    """返回 (status, path) 其中 status ∈ {'created', 'skipped_exists', 'skipped_invalid'}

    短名策略下的去重规则：
    - 同名笔记（vault 内任意文件夹）若 frontmatter paper_id == 当前 arxiv_id：视为同一篇，跳过
    - paper_id 不同：短名冲突，追加 _<arxiv_id> 后缀重算路径
    - 没有 paper_id 字段：保守跳过（可能是历史手写笔记，不覆盖）
    """
    title = paper.get("title", "").strip()
    if not title:
        return "skipped_invalid", None

    base_stem = paper.get("note_filename") or sanitize_filename(title)
    domain_folder = resolve_domain_folder(paper.get("matched_domain", ""))
    note_dir = os.path.join(vault_root, "20_Research", "Papers", domain_folder)

    arxiv_id = extract_arxiv_id(paper.get("id", "") or paper.get("arxiv_id", ""))
    aid_suffix = re.sub(r'[ /\\:*?"<>|]+', '_', arxiv_id).strip('_')

    def resolve_conflict(stem: str, path: str) -> tuple:
        """若同名已存在：比对 paper_id，决定是跳过还是换后缀。返回 (final_stem, final_path, skipped_path_or_None)"""
        existing_pid = _read_fm_paper_id(path)
        if existing_pid and arxiv_id and existing_pid == arxiv_id:
            return stem, path, path  # 同一篇
        if not existing_pid:
            return stem, path, path  # 保守：不覆盖无 paper_id 的历史文件
        # 真冲突：不同论文抢占了同一短名
        if not aid_suffix:
            return stem, path, path  # 当前论文没有 arxiv_id，无法区分，只能跳过
        new_stem = f"{stem}_{aid_suffix}"
        return new_stem, os.path.join(note_dir, f"{new_stem}.md"), None

    note_stem = base_stem
    note_path = os.path.join(note_dir, f"{note_stem}.md")

    existing_path = existing_stems.get(note_stem.lower())
    if existing_path:
        note_stem, note_path, skip = resolve_conflict(note_stem, existing_path)
        if skip:
            return "skipped_exists", skip
    elif os.path.exists(note_path):
        note_stem, note_path, skip = resolve_conflict(note_stem, note_path)
        if skip:
            return "skipped_exists", skip

    # 换过后缀后，再做一次幂等检查（不太可能同时三篇都抢同一短名，但防御性处理）
    if note_stem != base_stem:
        if existing_stems.get(note_stem.lower()) or os.path.exists(note_path):
            return "skipped_exists", note_path

    if dry_run:
        existing_stems[note_stem.lower()] = note_path
        return "created", note_path

    os.makedirs(note_dir, exist_ok=True)
    content = build_placeholder(paper, today, note_stem=note_stem)
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(content)
    existing_stems[note_stem.lower()] = note_path
    return "created", note_path


def main():
    # Force UTF-8 on stdout so non-ASCII paths/checkmarks don't crash on GBK consoles.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(
        description="为 arxiv_filtered.json 中的论文生成占位笔记（ADAPT 风格）"
    )
    parser.add_argument("--input", required=True, help="arxiv_filtered.json 路径")
    parser.add_argument("--vault", default=None, help="Obsidian vault 根目录")
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="从第几篇开始生成（1-based，包含）。list-only 默认 1；完整模式可设 4 跳过前3篇",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=0,
        help="到第几篇为止（1-based，包含）；0 表示全部",
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印将要创建的文件，不写入磁盘")
    parser.add_argument(
        "--preview",
        type=int,
        default=0,
        help="预览指定序号（1-based）论文的占位笔记完整内容到 stdout，不写盘；0 表示不预览",
    )
    args = parser.parse_args()

    vault_root = get_vault_path(args.vault)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error("读取 %s 失败: %s", args.input, e)
        sys.exit(1)

    papers = data.get("top_papers", [])
    if not papers:
        logger.warning("top_papers 为空，什么也不做")
        return

    if args.preview > 0:
        idx = args.preview - 1
        if 0 <= idx < len(papers):
            today = datetime.now().strftime("%Y-%m-%d")
            print(build_placeholder(papers[idx], today))
        else:
            logger.error("--preview 序号 %d 越界（共 %d 篇）", args.preview, len(papers))
            sys.exit(1)
        return

    start_idx = max(0, args.start - 1)
    end_idx = len(papers) if args.end <= 0 else min(len(papers), args.end)
    target = papers[start_idx:end_idx]

    today = datetime.now().strftime("%Y-%m-%d")
    stats = {"created": 0, "skipped_exists": 0, "skipped_invalid": 0}
    existing_stems = build_existing_stems(vault_root)

    for paper in target:
        status, path = write_placeholder(
            vault_root, paper, today, existing_stems, dry_run=args.dry_run
        )
        stats[status] += 1
        if path:
            rel = os.path.relpath(path, vault_root)
            tag = "[DRY] " if args.dry_run and status == "created" else ""
            if status == "created":
                print(f"[OK]  {tag}占位已生成: {rel}")
            elif status == "skipped_exists":
                print(f"[--]  已存在，跳过: {rel}")

    print(
        f"\n统计: 生成 {stats['created']} / 跳过已存在 {stats['skipped_exists']} / 跳过无效 {stats['skipped_invalid']}"
        + ("（dry-run，未实际写入）" if args.dry_run else "")
    )


if __name__ == "__main__":
    main()
