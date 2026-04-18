"""Generate a --list-only recommendation note from arxiv_filtered.json.

One-off helper invoked by the start-my-day skill in list-only mode.
"""
import json
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


def fmt_authors(authors, n=3):
    if not authors:
        return "--"
    normalized = []
    for a in authors:
        if isinstance(a, str):
            normalized.append(a)
        elif isinstance(a, dict):
            normalized.append(a.get("name") or a.get("full_name") or str(a))
        else:
            normalized.append(str(a))
    first = normalized[:n]
    suffix = " 等" if len(normalized) > n else ""
    return ", ".join(first) + suffix


def clean_title(t):
    return t.replace("\ufffd\ufffd", "π").replace("��", "π").strip()


def first_sentence(s, cap=260):
    s = re.sub(r"\s+", " ", s).strip()
    m = re.match(r"([^.]{20,300}\.)", s)
    if m:
        out = m.group(1)
    else:
        out = s[:cap] + ("..." if len(s) > cap else "")
    return out.strip()


def main():
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vault = os.environ.get("OBSIDIAN_VAULT_PATH", r"C:\Users\84372\Documents\Papers")

    with open(os.path.join(skill_dir, "arxiv_filtered.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(skill_dir, "existing_notes_index.json"), "r", encoding="utf-8") as f:
        notes_idx = json.load(f)

    papers = data["top_papers"][:50]

    existing_by_stem = {}
    existing_by_title = {}
    for n in notes_idx.get("notes", []):
        stem = n["filename"].replace(".md", "").lower()
        existing_by_stem[stem] = n["path"]
        if n.get("title"):
            existing_by_title[n["title"].lower().strip()] = n["path"]

    stopwords = {
        "for", "with", "via", "and", "from", "the", "into", "under", "using",
        "based", "model", "models", "learning", "data", "multi", "towards",
        "toward", "new", "more", "less", "our", "this", "are", "can",
    }
    kw_counts = {}
    for p in papers:
        for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", p["title"]):
            lw = w.lower()
            if lw in stopwords or lw.isdigit():
                continue
            kw_counts[w] = kw_counts.get(w, 0) + 1
    top_keywords = [k for k, _ in sorted(kw_counts.items(), key=lambda kv: -kv[1])[:15]]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = (
        "---\n"
        f"keywords: [{', '.join(top_keywords)}]\n"
        "tags: [\"llm-generated\", \"daily-paper-recommend\"]\n"
        "run: 1\n"
        "---\n\n"
        f"> 本次运行：第 1 次 / 生成时间：{now_str} / 模式：--list-only（50 篇候选清单）\n\n"
        "## 今日概览\n\n"
        "今日筛选了 50 篇论文，主要聚焦于**模仿学习与扩散策略**、**机器人强化学习**、**3D 场景理解与感知**以及 **Loco-Manipulation 全身控制**等前沿方向。\n\n"
        "- **总体趋势**：VLA（Vision-Language-Action）与世界模型类工作在榜单前列显著领先；扩散/流匹配策略继续向更多策略学习与对齐任务扩散；3D Gaussian Splatting 相关工作（TokenGS、GlobalSplat、NG-GS）集中涌现。\n"
        "- **质量分布**：推荐评分在 **6.09–8.77** 之间，均值约 **6.66**，前 5 篇评分 ≥ 8.0，属当日重点。\n"
        "- **研究热点**：\n"
        "  - **隐式规划的 VLA**：榜首 World-Value-Action Model 把隐式 planning 融入 VLA；π0.5 强调开放世界泛化。\n"
        "  - **数据高效 + 全身控制**：DockAnywhere 移动操作、Switch 人形敏捷切换、CART 地形适应共同体现\"少数据+硬件闭环\"的主旋律。\n"
        "  - **3D 表示 + 分割/重建**：NG-GS、TokenGS、GlobalSplat、Geometric Context Transformer 在 GS 表示与流式重建上持续精进。\n"
        "  - **RL × 语言/代码**：MARS²、Flow-GRPO、LongAct 把 RL 从控制推到多智能体/长上下文/流匹配。\n"
        "- **阅读建议**：\n"
        "  1. 先读前 5 篇（评分 ≥ 8.0），直接关联 loco-manipulation + VLA 研究方向；\n"
        "  2. 再选第 6–15 篇中与 SONIC-style WBC 工作重叠的 3–4 篇；\n"
        "  3. 剩余为\"了解趋势\"级别，可只读 TL;DR。\n\n"
        "---\n\n"
        "## 论文清单（按推荐评分从高到低）\n\n"
    )

    lines = []
    for idx, p in enumerate(papers, 1):
        title = clean_title(p["title"])
        score = p["scores"]["recommendation"]
        authors = fmt_authors(p.get("authors", []))
        cats = ", ".join(p.get("categories", [])[:3]) or "--"
        pub = (p.get("published_date") or "")[:10] or "--"
        arxiv_url = p.get("url", "").replace("http://", "https://")
        pdf_url = p.get("pdf_url", "")
        note_fn = p.get("note_filename", "")
        summary = p.get("summary", "")
        tldr = first_sentence(summary)

        # Always use bare stem so all daily notes link to a single graph node
        # per paper, regardless of whether the note existed at generation time.
        # Obsidian resolves bare stems vault-wide; conflicting basenames are
        # surfaced by the verify_wikilinks helper.
        target_stem = note_fn
        if note_fn.lower() not in existing_by_stem and title.lower() in existing_by_title:
            existing_path = existing_by_title[title.lower()]
            target_stem = os.path.basename(existing_path).replace(".md", "")
        wl = f"[[{target_stem}|{title}]]"

        lines.append(f"### {idx}. {wl} — 评分：{score:.2f}")
        lines.append(f"- **作者**：{authors}")
        lines.append(f"- **分类**：{cats}  |  **发布**：{pub}  |  **链接**：[arXiv]({arxiv_url}) | [PDF]({pdf_url})")
        lines.append(f"- **一句话**：{tldr}")
        lines.append("")

    content = header + "\n".join(lines)

    out = os.path.join(vault, "10_Daily", "2026-04-18论文推荐.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {out} ({len(content)} chars, {len(papers)} papers)")


if __name__ == "__main__":
    main()
