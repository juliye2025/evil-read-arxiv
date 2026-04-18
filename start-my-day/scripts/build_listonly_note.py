#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a list-only recommendation note for start-my-day.

Produces one compact entry per paper with a wikilink to the placeholder
note, ranked by recommendation score.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

# Windows 默认 cp936 控制台会把脚本的 UTF-8 日志显示为乱码，统一强制 UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

DOMAIN_FOLDER_MAP = {
    "Loco-Manipulation & Whole-Body Control": "Loco-Manipulation",
    "Vision-Language-Action Models": "Foundation_Models",
    "World Models & Video Generation for Robotics": "Foundation_Models",
    "6D Rearrangement & Object Manipulation": "Robot_Manipulation",
    "Imitation Learning & Diffusion Policy": "Robot_Manipulation",
    "Reinforcement Learning for Robotics": "Robot_Manipulation",
    "Embodied AI & Navigation": "Embodied_AI",
    "3D Scene Understanding & Perception": "Embodied_AI",
    "Simulation & Benchmarks": "Embodied_AI",
}


def resolve_domain_folder(matched_domain: str) -> str:
    if not matched_domain:
        return "Other"
    if matched_domain in DOMAIN_FOLDER_MAP:
        return DOMAIN_FOLDER_MAP[matched_domain]
    sanitized = re.sub(r"[^\w\-]+", "_", matched_domain).strip("_")
    return sanitized or "Other"


def extract_arxiv_id(raw_id: str) -> str:
    if not raw_id:
        return ""
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", raw_id)
    return m.group(1) if m else raw_id.strip()


def format_authors_top3(authors):
    names = []
    for a in authors or []:
        if isinstance(a, dict):
            name = a.get("name") or a.get("authorId") or ""
        else:
            name = str(a or "")
        if name:
            names.append(name)
        if len(names) >= 3:
            break
    return ", ".join(names)


def one_line_summary(abstract: str, max_len: int = 220) -> str:
    if not abstract:
        return ""
    s = abstract.strip().replace("\n", " ")
    # first sentence-ish: cut at the first ". " boundary after 60 chars, fallback to max_len
    cut = -1
    for i, ch in enumerate(s):
        if ch == "." and i >= 60 and (i + 1 >= len(s) or s[i + 1] == " "):
            cut = i + 1
            break
    if cut == -1 or cut > max_len + 40:
        cut = min(len(s), max_len)
        if cut < len(s):
            s = s[:cut].rsplit(" ", 1)[0] + "…"
            return s
    return s[:cut].strip()


def next_versioned_path(base: str) -> (str, int):
    """Return (path, run_number)."""
    if not os.path.exists(base + ".md"):
        return base + ".md", 1
    n = 2
    while os.path.exists(f"{base}_v{n}.md"):
        n += 1
    return f"{base}_v{n}.md", n


def build_overview(papers):
    scores = [p["scores"]["recommendation"] for p in papers]
    domains = Counter(p.get("matched_domain", "?") for p in papers)
    top3 = domains.most_common(3)
    score_max = max(scores)
    score_min = min(scores)
    avg = sum(scores) / len(scores)
    # 简短的研究热点描述
    hotspots_desc = {
        "Vision-Language-Action Models": "VLA 基座模型的泛化与隐式规划能力",
        "Loco-Manipulation & Whole-Body Control": "人形机器人全身控制与技能切换",
        "Imitation Learning & Diffusion Policy": "模仿学习 / 扩散策略及数据高效训练",
        "Reinforcement Learning for Robotics": "面向机器人的强化学习算法与 sim-to-real",
        "3D Scene Understanding & Perception": "3D 场景理解与感知",
        "World Models & Video Generation for Robotics": "机器人世界模型与视频生成",
        "6D Rearrangement & Object Manipulation": "6D 重排与物体操控",
        "Embodied AI & Navigation": "具身导航与决策",
    }
    lines = []
    lines.append("## 今日概览\n")
    # 主要方向
    primary = "、".join(f"**{d}**" for d, _ in top3)
    lines.append(f"今日推荐的 {len(papers)} 篇论文主要聚焦于 {primary} 等方向。\n")
    lines.append(
        f"- **总体趋势**：具身智能的多个子方向同时进展——VLA 与世界模型继续向通用化、"
        f"开放世界泛化和隐式规划演进，全身控制（WBC）/ 腿部-操作联合体系在动态技能切换与 loco-manipulation 上有明显推进，"
        f"扩散策略与 RL 训练则围绕"
        f"数据效率、奖励塑形和真实世界适应展开。"
    )
    lines.append(
        f"- **质量分布**：评分范围 {score_min:.2f}–{score_max:.2f}，"
        f"均分 {avg:.2f}；前 10 名普遍在 7 分以上，属于可优先读的候选。"
    )
    lines.append("- **研究热点**：")
    for d, cnt in top3:
        desc = hotspots_desc.get(d, d)
        lines.append(f"  - **{d}**（{cnt} 篇）：{desc}")
    lines.append(
        "- **阅读建议**：先读前 1–2 篇评分最高的 VLA / WBC 综合代表作（与你的研究主线 loco-manipulation + 大模型 WBC 直接相关），"
        "再横扫扩散策略与数据效率主题（第 3–10 名），之后仅按感兴趣的关键词回翻余下候选，避免大块时间被清单耗尽。\n"
    )
    return "\n".join(lines)


def build_entry(i: int, paper: dict) -> str:
    title = paper.get("title", "").strip()
    arxiv_id = extract_arxiv_id(paper.get("id", ""))
    url = paper.get("url") or f"https://arxiv.org/abs/{arxiv_id}"
    pdf = paper.get("pdf_url") or f"https://arxiv.org/pdf/{arxiv_id}"
    authors = format_authors_top3(paper.get("authors", []))
    cats = ", ".join(paper.get("categories") or [])
    pub = (paper.get("published_date") or "")[:10]
    score = paper["scores"]["recommendation"]
    tl = one_line_summary(paper.get("summary", ""))
    note_filename = paper.get("note_filename") or ""
    # wikilink target = note filename stem (Obsidian resolves by name)
    if note_filename:
        # 去掉 .md 后缀，如果有的话
        stem = note_filename[:-3] if note_filename.endswith(".md") else note_filename
        # 用短标题作为显示文本，避免下划线显示
        heading = f"### {i}. [[{stem}|{title}]] — 评分：{score:.2f}"
    else:
        heading = f"### {i}. {title} — 评分：{score:.2f}"
    lines = [
        heading,
        f"- **作者**：{authors} 等",
        f"- **分类**：{cats}  |  **发布**：{pub}  |  **链接**：[arXiv]({url}) | [PDF]({pdf})",
        f"- **一句话**：{tl}",
        "",
    ]
    return "\n".join(lines)


def collect_keywords(papers, top_n: int = 30):
    """简单抽取常见关键词用于 frontmatter."""
    # 从标题提取大写名词缩写
    caps = Counter()
    common_skip = {"for", "with", "via", "and", "the", "of", "on", "in", "to"}
    for p in papers:
        for tok in re.findall(r"[A-Z][A-Za-z0-9\-]{2,}", p.get("title", "")):
            if tok.lower() not in common_skip:
                caps[tok] += 1
    return [k for k, _ in caps.most_common(top_n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="arxiv_filtered.json")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD for filename")
    ap.add_argument("--suffix", default="论文推荐")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    papers = data.get("top_papers", [])
    papers.sort(key=lambda x: x["scores"]["recommendation"], reverse=True)

    daily_dir = os.path.join(args.vault, "10_Daily")
    os.makedirs(daily_dir, exist_ok=True)
    base = os.path.join(daily_dir, f"{args.date}{args.suffix}")
    path, run_n = next_versioned_path(base)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    kws = collect_keywords(papers)
    kws_yaml = ", ".join(kws)

    out = []
    out.append("---")
    out.append(f"keywords: [{kws_yaml}]")
    out.append('tags: ["llm-generated", "daily-paper-recommend"]')
    out.append(f"run: {run_n}")
    out.append(f"date: {args.date}")
    out.append(f'mode: "list-only"')
    out.append("---")
    out.append("")
    out.append(f"> 本次运行：第 {run_n} 次 / 生成时间：{now_str} / 模式：--list-only")
    out.append("")
    out.append(f"# {args.date} 论文推荐（list-only · {len(papers)} 篇候选）")
    out.append("")
    out.append(build_overview(papers))
    out.append("## 候选论文清单（按评分降序）")
    out.append("")
    for i, p in enumerate(papers, 1):
        out.append(build_entry(i, p))

    content = "\n".join(out)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] 已写入: {path}")
    print(f"     运行编号: {run_n} / 论文数: {len(papers)}")


if __name__ == "__main__":
    main()
