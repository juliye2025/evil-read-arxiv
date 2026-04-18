#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新知识图谱脚本
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime

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


def make_short_title(title: str, max_len: int = 32) -> str:
    """提取论文短标题用于图谱节点显示。

    策略（按优先级）：
    1. 冒号前部分（"π0.5: a Vision-Language-Action..." → "π0.5"）
    2. 破折号前部分（em/en/hyphen，仅在冒号结果仍过长时尝试）
    3. 兜底：在词边界截断 max_len 字符 + 省略号（避免切到词中间）

    短标题保留 Unicode 字符（π、σ 等），不做大小写转换。
    """
    if not title:
        return title
    short = title.split(':', 1)[0].strip()
    if len(short) > max_len:
        for sep in (' — ', ' – '):
            if sep in short:
                short = short.split(sep, 1)[0].strip()
                break
    if len(short) > max_len:
        truncated = short[: max_len - 1]
        last_space = truncated.rfind(' ')
        # 仅在词边界落在后半段才用，否则强行截断也比奇怪的极短词好
        if last_space > max_len // 2:
            truncated = truncated[:last_space]
        short = truncated.rstrip(' ,;-.') + '…'
    return short or title


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='更新知识图谱 / Update knowledge graph')
    parser.add_argument('--paper-id', type=str, help='论文 arXiv ID / Paper arXiv ID (单篇模式必填)')
    parser.add_argument('--title', type=str, help='论文标题 / Paper title (单篇模式必填)')
    parser.add_argument('--domain', type=str, help='论文领域 / Paper domain (单篇模式必填)')
    parser.add_argument('--score', type=float, default=0.0, help='质量评分 / Quality score')
    parser.add_argument('--related', type=str, nargs='*', default=[], help='相关论文ID列表 / Related paper IDs')
    parser.add_argument('--vault', type=str, default=None, help='Obsidian vault 路径 / Obsidian vault path')
    parser.add_argument('--language', type=str, default='zh', choices=['zh', 'en'], help='语言 / Language: zh (中文) or en (English)')
    parser.add_argument('--analyzed', dest='analyzed', action='store_true', default=True,
                        help='标记为已深度分析 (默认 True)')
    parser.add_argument('--no-analyzed', dest='analyzed', action='store_false',
                        help='仅登记节点，未深度分析 (list-only 批量模式用)')
    parser.add_argument('--batch-json', type=str, default=None,
                        help='批量模式：从 arxiv_filtered.json 读取 top_papers 批量登记节点。'
                             '已存在且 analyzed=True 的节点不会被覆盖')
    parser.add_argument('--migrate-titles', action='store_true',
                        help='一次性迁移模式：将现有节点的 title 重写为简称（用于 Obsidian 图谱显示），'
                             '原 title 保存到 full_title。已有 full_title 的节点跳过。')
    args = parser.parse_args()

    if not args.batch_json and not args.migrate_titles:
        missing = [n for n, v in (('--paper-id', args.paper_id),
                                   ('--title', args.title),
                                   ('--domain', args.domain)) if not v]
        if missing:
            parser.error(f"单篇模式缺少必填参数: {', '.join(missing)}")

    vault_root = get_vault_path(args.vault)
    date = datetime.now().strftime("%Y-%m-%d")

    graph_dir = os.path.join(vault_root, "20_Research", "PaperGraph")
    os.makedirs(graph_dir, exist_ok=True)
    graph_path = os.path.join(graph_dir, "graph_data.json")

    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph = json.load(f)
    except FileNotFoundError:
        graph = {
            "nodes": [],
            "edges": [],
            "last_updated": date
        }

    # 兼容两种节点存储格式：list[dict] 或 dict[id -> dict]。记录原始格式用于回写。
    nodes_raw = graph.get("nodes", [])
    if isinstance(nodes_raw, dict):
        nodes_format = "dict"
        nodes_by_id = {k: v for k, v in nodes_raw.items() if isinstance(v, dict)}
    else:
        nodes_format = "list"
        nodes_by_id = {}
        for node in nodes_raw:
            if isinstance(node, dict) and node.get("id"):
                nodes_by_id[node["id"]] = node

    def upsert_node(paper_id, title, domain, score, year, analyzed, language):
        """插入或更新节点。已存在且 analyzed=True 的节点只更新 quality_score（取较大值）。

        节点的 `title` 字段存储简称（用于 Obsidian 图谱显示），
        完整标题保存在 `full_title`，避免信息丢失。
        """
        if language == "zh":
            tags = ["论文笔记", domain]
        else:
            tags = ["paper-notes", domain]

        short = make_short_title(title)
        new_node = {
            "id": paper_id,
            "title": short,
            "full_title": title,
            "year": year,
            "domain": domain,
            "quality_score": score,
            "tags": tags,
            "analyzed": analyzed,
        }

        if paper_id in nodes_by_id:
            existing = nodes_by_id[paper_id]
            if existing.get("analyzed") and not analyzed:
                # 已深度分析的节点不被 list-only 批量登记覆盖，只可能抬高分
                if score > existing.get("quality_score", 0):
                    existing["quality_score"] = score
                return "kept"
            existing.update(new_node)
            return "updated"
        else:
            nodes_by_id[paper_id] = new_node
            return "added"

    stats = {"added": 0, "updated": 0, "kept": 0, "migrated": 0, "migrate_skipped": 0}

    if args.migrate_titles:
        # ===== 标题简称迁移模式（幂等） =====
        # full_title 是源文件，每次都从 full_title 重新计算 short title。
        # 若节点尚无 full_title，则用当前 title 初始化。
        for nid, node in nodes_by_id.items():
            if not isinstance(node, dict):
                continue
            full = node.get("full_title") or node.get("title", "")
            if not full:
                stats["migrate_skipped"] += 1
                continue
            new_short = make_short_title(full)
            old_title = node.get("title", "")
            node["full_title"] = full
            if new_short == old_title:
                stats["migrate_skipped"] += 1
            else:
                node["title"] = new_short
                stats["migrated"] += 1
    elif args.batch_json:
        # ===== 批量登记模式 =====
        try:
            with open(args.batch_json, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error("读取批量 JSON 失败: %s", e)
            sys.exit(1)

        top_papers = batch_data.get('top_papers', [])
        for p in top_papers:
            paper_id = p.get('arxiv_id') or p.get('id')
            title = p.get('title', '').strip()
            if not paper_id or not title:
                continue
            domain = p.get('matched_domain') or ('未分类' if args.language == 'zh' else 'uncategorized')
            score = float(p.get('scores', {}).get('recommendation', 0.0))
            pub = p.get('published_date') or p.get('published') or ''
            try:
                year = int(str(pub)[:4])
            except (ValueError, TypeError):
                year = datetime.now().year
            result = upsert_node(paper_id, title, domain, score, year,
                                 analyzed=args.analyzed, language=args.language)
            stats[result] += 1
    else:
        # ===== 单篇模式 =====
        try:
            year = int(date[:4])
        except (ValueError, IndexError):
            year = datetime.now().year
        result = upsert_node(args.paper_id, args.title, args.domain, args.score,
                             year, analyzed=args.analyzed, language=args.language)
        stats[result] += 1

        if args.related:
            existing_edges = {
                (edge.get("source"), edge.get("target"))
                for edge in graph["edges"]
                if edge.get("source") and edge.get("target")
            }
            for related_id in args.related:
                if related_id and related_id != args.paper_id and (args.paper_id, related_id) not in existing_edges:
                    graph["edges"].append({
                        "source": args.paper_id,
                        "target": related_id,
                        "type": "related",
                        "weight": 0.7
                    })

    graph["last_updated"] = date
    # 以读入时的相同格式写回（保持向后兼容）
    if nodes_format == "dict":
        graph["nodes"] = nodes_by_id
    else:
        graph["nodes"] = list(nodes_by_id.values())

    try:
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
    except (IOError, TypeError) as e:
        logger.error("写入图谱失败: %s", e)
        sys.exit(1)

    if args.language == "zh":
        print(f"图谱已更新: {graph_path}")
        print(f"节点数: {len(nodes_by_id)}  边数: {len(graph['edges'])}")
        if args.batch_json:
            print(f"批量登记: 新增 {stats['added']} / 更新 {stats['updated']} / 保留已分析 {stats['kept']}")
        if args.migrate_titles:
            print(f"标题迁移: 简称化 {stats['migrated']} / 已是简称或已迁移 {stats['migrate_skipped']}")
    else:
        print(f"Graph updated: {graph_path}")
        print(f"Nodes: {len(nodes_by_id)}  Edges: {len(graph['edges'])}")
        if args.batch_json:
            print(f"Batch: added {stats['added']} / updated {stats['updated']} / kept-analyzed {stats['kept']}")
        if args.migrate_titles:
            print(f"Title migration: shortened {stats['migrated']} / already-short {stats['migrate_skipped']}")


if __name__ == '__main__':
    main()
