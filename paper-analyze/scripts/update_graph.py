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


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='更新知识图谱')
    parser.add_argument('--paper-id', type=str, required=True, help='论文 arXiv ID')
    parser.add_argument('--title', type=str, required=True, help='论文标题')
    parser.add_argument('--domain', type=str, required=True, help='论文领域')
    parser.add_argument('--score', type=float, default=0.0, help='质量评分')
    parser.add_argument('--related', type=str, nargs='*', default=[], help='相关论文ID列表')
    parser.add_argument('--vault', type=str, default=None, help='Obsidian vault 路径')
    args = parser.parse_args()

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

    try:
        year = int(date[:4])
    except (ValueError, IndexError):
        year = datetime.now().year

    paper_node = {
        "id": args.paper_id,
        "title": args.title,
        "year": year,
        "domain": args.domain,
        "quality_score": args.score,
        "tags": ["论文笔记", args.domain],
        "analyzed": True
    }

    # 安全构建节点索引（跳过无 id 的节点）
    existing_nodes = {
        node.get("id"): i
        for i, node in enumerate(graph["nodes"])
        if node.get("id")
    }
    if args.paper_id in existing_nodes:
        graph["nodes"][existing_nodes[args.paper_id]].update(paper_node)
    else:
        graph["nodes"].append(paper_node)

    if args.related:
        # 安全构建边索引（跳过无 source/target 的边）
        existing_edges = {
            (edge.get("source"), edge.get("target"))
            for edge in graph["edges"]
            if edge.get("source") and edge.get("target")
        }
        for related_id in args.related:
            # 防止自引用
            if related_id and related_id != args.paper_id and (args.paper_id, related_id) not in existing_edges:
                graph["edges"].append({
                    "source": args.paper_id,
                    "target": related_id,
                    "type": "related",
                    "weight": 0.7
                })

    graph["last_updated"] = date

    try:
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
    except (IOError, TypeError) as e:
        logger.error("写入图谱失败: %s", e)
        sys.exit(1)

    print(f"图谱已更新: {graph_path}")
    print(f"节点数: {len(graph['nodes'])}")
    print(f"边数: {len(graph['edges'])}")


if __name__ == '__main__':
    main()
