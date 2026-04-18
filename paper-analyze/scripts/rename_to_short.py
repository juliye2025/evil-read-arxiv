#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量重命名 20_Research/Papers/ 下的笔记为简称文件名，并同步重写所有 wikilink。

为什么需要这个脚本：
    Obsidian 原生图谱节点 label 来源于文件名（不是 frontmatter title），
    长文件名让图谱视图很难看清。本脚本把文件名改成 make_short_title() 的简称，
    同时把整个 vault 内的 wikilink 同步替换。

策略：
    1. 扫描 Papers/ 下所有 .md，从 frontmatter `title` 或文件名推断完整标题。
    2. 调用 make_short_title 计算短名 → sanitized 文件名 stem。
    3. 检测同文件夹内的简称冲突；若有冲突，给冲突项追加 arxiv_id（或序号）。
    4. 全 vault 扫描 .md，把指向旧 stem 的 wikilink 替换为新 stem。
       支持 [[stem]]、[[stem|alias]]、[[folder/stem]]、[[folder/stem|alias]]
       裸 [[stem]] 替换时自动追加完整原标题作为 alias，避免显示丢失。
    5. 用 os.rename 物理重命名文件。
    6. 同步更新 graph_data.json 中节点的 note_path（如有）。

默认是 --dry-run，--apply 才真正执行。
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# 复用 update_graph.py 里的简称算法
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from update_graph import make_short_title  # noqa: E402


PAPERS_SUBDIR = os.path.join("20_Research", "Papers")
GRAPH_PATH = os.path.join("20_Research", "PaperGraph", "graph_data.json")


def to_safe_filename(s: str) -> str:
    """文件名安全化（与 search_arxiv.title_to_note_filename 同规则）。"""
    return re.sub(r'[ /\\:*?"<>|]+', "_", s).strip("_")


def read_frontmatter_title(path: str) -> str:
    """从 .md 的 YAML frontmatter 读 title 字段；找不到则返回空串。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(3000)
    except (IOError, OSError):
        return ""
    if not head.startswith("---"):
        return ""
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', head, re.M)
    return m.group(1).strip() if m else ""


def read_frontmatter_paper_id(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(3000)
    except (IOError, OSError):
        return ""
    m = re.search(r'^paper_id:\s*["\']?([\d.]+)["\']?\s*$', head, re.M)
    return m.group(1).strip() if m else ""


def collect_notes(papers_dir: str) -> List[Dict]:
    notes = []
    for root, _, files in os.walk(papers_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            path = os.path.join(root, fname)
            stem = fname[:-3]
            title = read_frontmatter_title(path) or stem.replace("_", " ")
            notes.append(
                {
                    "stem": stem,
                    "title": title,
                    "path": path,
                    "folder": os.path.dirname(path),
                    "paper_id": read_frontmatter_paper_id(path),
                }
            )
    return notes


def compute_renames(notes: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """返回 (renames, conflicts)。renames 中每项包含 old_stem / new_stem / 等。"""
    for n in notes:
        n["short"] = make_short_title(n["title"])
        n["short_stem"] = to_safe_filename(n["short"])

    # 冲突检测：同一文件夹内的 short_stem 若被多个文件抢占
    folder_map: Dict[str, Dict[str, List[Dict]]] = {}
    for n in notes:
        folder_map.setdefault(n["folder"], {}).setdefault(n["short_stem"], []).append(n)

    conflicts = []
    for folder, sm in folder_map.items():
        for short_stem, group in sm.items():
            if len(group) > 1:
                conflicts.append({"folder": folder, "short_stem": short_stem, "files": group})
                # 自动用 paper_id 后缀拆分（如 ADAPT_2604.14732）；没有 paper_id 的退化为序号
                for i, n in enumerate(group):
                    suffix = n["paper_id"] or str(i + 1)
                    n["short_stem"] = f"{short_stem}_{suffix}"

    renames = []
    for n in notes:
        if n["short_stem"] != n["stem"]:
            renames.append(
                {
                    "old_stem": n["stem"],
                    "new_stem": n["short_stem"],
                    "old_path": n["path"],
                    "new_path": os.path.join(n["folder"], n["short_stem"] + ".md"),
                    "title": n["title"],
                }
            )
    return renames, conflicts


def build_wikilink_pattern(old_stems: List[str]) -> re.Pattern:
    """构造一个正则，匹配 vault 中所有 wikilink（含可选文件夹前缀、可选 .md 后缀、可选 alias）。

    捕获组：
      1: 整段文件夹前缀（含末尾 /），如 '20_Research/Papers/Foundation_Models/'，可能为空
      2: 旧 stem
      3: 可选的 '.md' 后缀（Obsidian 允许 wikilink 带扩展名）
      4: '|alias' 部分，可能为空
    """
    if not old_stems:
        return re.compile(r"(?!x)x")
    sorted_stems = sorted(old_stems, key=len, reverse=True)
    escaped = "|".join(re.escape(s) for s in sorted_stems)
    return re.compile(
        r"\[\[((?:[^\]\[|]+/)?)(" + escaped + r")(\.md)?(\|[^\]]*)?\]\]"
    )


def rewrite_wikilinks_in_text(
    text: str, rename_map: Dict[str, Dict], pattern: re.Pattern
) -> Tuple[str, int]:
    """把文本中的 wikilink 旧 stem 替换为新 stem。

    rename_map: old_stem -> {'new_stem': str, 'title': str}
    返回 (新文本, 替换数量)
    """
    count = 0

    def replace(m: re.Match) -> str:
        nonlocal count
        prefix = m.group(1) or ""
        old_stem = m.group(2)
        ext = m.group(3) or ""  # 可能是 ".md" 或空
        alias = m.group(4) or ""
        info = rename_map.get(old_stem)
        if not info:
            return m.group(0)
        new_stem = info["new_stem"]
        if not alias:
            # 裸 wikilink → 用完整原标题作 alias，避免显示从长名变成超短名
            full_title = info["title"]
            alias = f"|{full_title}"
        count += 1
        return f"[[{prefix}{new_stem}{ext}{alias}]]"

    return pattern.sub(replace, text), count


def scan_vault_for_wikilinks(
    vault: str, rename_map: Dict[str, Dict], skip_dirs=(".obsidian", ".trash", ".git")
) -> List[Tuple[str, int, str]]:
    """扫描 vault 内所有 .md，返回需要改动的 (path, count, new_text)。

    自动跳过 .backup_* 目录，避免污染本脚本之前生成的备份。
    """
    pattern = build_wikilink_pattern(list(rename_map.keys()))
    pending = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs
                   if d not in skip_dirs and not d.startswith(".backup_")]
        for fname in files:
            if not fname.endswith(".md"):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except (IOError, OSError, UnicodeDecodeError):
                continue
            new_text, count = rewrite_wikilinks_in_text(text, rename_map, pattern)
            if count > 0:
                pending.append((path, count, new_text))
    return pending


def update_graph_paths(graph_path: str, rename_map: Dict[str, Dict]) -> int:
    """更新 graph_data.json 中节点的 note_path 字段。"""
    if not os.path.exists(graph_path):
        return 0
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)
    nodes_raw = graph.get("nodes", [])
    nodes_iter = nodes_raw.values() if isinstance(nodes_raw, dict) else nodes_raw
    changed = 0
    for node in nodes_iter:
        if not isinstance(node, dict):
            continue
        note_path = node.get("note_path", "")
        if not note_path:
            continue
        # note_path 可能形如 '20_Research/Papers/Foundation_Models/OldStem.md'
        old_basename = os.path.basename(note_path).replace(".md", "")
        info = rename_map.get(old_basename)
        if not info:
            continue
        new_path = note_path.replace(old_basename + ".md", info["new_stem"] + ".md")
        node["note_path"] = new_path
        changed += 1
    if changed:
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
    return changed


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description="重命名 paper 笔记为简称并同步 wikilink")
    parser.add_argument("--vault", type=str,
                        default=os.environ.get("OBSIDIAN_VAULT_PATH", ""),
                        help="vault 根目录（默认从 OBSIDIAN_VAULT_PATH）")
    parser.add_argument("--apply", action="store_true",
                        help="实际执行改动（默认 dry-run，仅打印计划）")
    parser.add_argument("--limit-preview", type=int, default=20,
                        help="dry-run 时最多打印多少条样例（默认 20）")
    args = parser.parse_args()

    if not args.vault or not os.path.isdir(args.vault):
        logger.error("vault 路径无效: %s", args.vault)
        return 1

    papers_dir = os.path.join(args.vault, PAPERS_SUBDIR)
    if not os.path.isdir(papers_dir):
        logger.error("Papers 目录不存在: %s", papers_dir)
        return 1

    notes = collect_notes(papers_dir)
    logger.info("收集到 %d 篇笔记", len(notes))

    renames, conflicts = compute_renames(notes)
    logger.info("需要重命名: %d / 总数: %d", len(renames), len(notes))
    if conflicts:
        logger.warning("文件夹内简称冲突 %d 组（已追加 paper_id/序号后缀消歧）:", len(conflicts))
        for c in conflicts:
            logger.warning("  %s/%s.md  ← %d 个文件", c["folder"], c["short_stem"], len(c["files"]))

    rename_map = {r["old_stem"]: {"new_stem": r["new_stem"], "title": r["title"]} for r in renames}
    pending_link_files = scan_vault_for_wikilinks(args.vault, rename_map)
    total_links = sum(c for _, c, _ in pending_link_files)
    logger.info("将改写 wikilink: %d 处, 涉及 %d 个文件", total_links, len(pending_link_files))

    graph_path = os.path.join(args.vault, GRAPH_PATH)

    # ------ 打印预览 ------
    print()
    print("=" * 70)
    print(f"{'[APPLY]' if args.apply else '[DRY-RUN]'} 重命名 + wikilink 改写预览")
    print("=" * 70)
    print(f"重命名文件数: {len(renames)}")
    print(f"涉及 wikilink: {total_links} 处 / {len(pending_link_files)} 个文件")
    print(f"冲突组数:     {len(conflicts)}")

    if renames:
        print(f"\n--- 前 {min(args.limit_preview, len(renames))} 个重命名预览 ---")
        for r in renames[: args.limit_preview]:
            print(f"  {r['old_stem'][:55]:55s}  →  {r['new_stem']}")

    if pending_link_files:
        print(f"\n--- 前 {min(args.limit_preview, len(pending_link_files))} 个 wikilink 改写文件 ---")
        for p, c, _ in pending_link_files[: args.limit_preview]:
            rel = os.path.relpath(p, args.vault)
            print(f"  [{c} 处] {rel}")

    if not args.apply:
        print("\n[DRY-RUN] 未执行任何改动。加 --apply 真正执行。")
        return 0

    # ------ 执行 ------
    # 步骤 1：先重写 wikilink（此时旧文件还在，安全）
    for path, _, new_text in pending_link_files:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    logger.info("已改写 %d 个文件的 wikilink", len(pending_link_files))

    # 步骤 2：物理重命名
    renamed = 0
    failed = 0
    for r in renames:
        try:
            os.rename(r["old_path"], r["new_path"])
            renamed += 1
        except OSError as e:
            logger.error("重命名失败 %s → %s: %s", r["old_path"], r["new_path"], e)
            failed += 1
    logger.info("文件重命名: 成功 %d / 失败 %d", renamed, failed)

    # 步骤 3：更新图谱 note_path
    graph_changed = update_graph_paths(graph_path, rename_map)
    logger.info("图谱 note_path 更新: %d 个节点", graph_changed)

    print(f"\n[DONE] 重命名 {renamed} / wikilink {total_links} 处 / 图谱 {graph_changed} 节点")
    return 0


if __name__ == "__main__":
    sys.exit(main())
