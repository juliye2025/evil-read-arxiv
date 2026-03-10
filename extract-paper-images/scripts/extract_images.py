#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文图片提取脚本 - 支持从arXiv源码包优先提取
优先级：
1. arXiv源码包中的pics/或figures/目录（真正的论文图片）
2. 源码包中的PDF图片（架构图、实验图等）
3. PDF直接提取的图片（最后备选）
"""

import fitz  # PyMuPDF
import os
import json
import sys
import re
import shutil
import tarfile
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False
    logger.warning("requests not found, using urllib")


def extract_arxiv_source(arxiv_id, temp_dir):
    """下载并提取arXiv源码包"""
    source_url = f"https://arxiv.org/e-print/{arxiv_id}"
    print(f"正在下载arXiv源码包: {source_url}")

    try:
        if HAS_REQUESTS:
            response = requests.get(source_url, timeout=60)
            content = response.content if response.status_code == 200 else None
            status = response.status_code
        else:
            try:
                req = urllib.request.urlopen(source_url, timeout=60)
                content = req.read()
                status = req.status
            except urllib.error.HTTPError as http_err:
                logger.error("HTTP错误 %d: %s", http_err.code, http_err.reason)
                return False

        if status == 200 and content:
            tar_path = os.path.join(temp_dir, f"{arxiv_id}.tar.gz")
            with open(tar_path, 'wb') as f:
                f.write(content)
            print(f"源码包已下载: {tar_path}")

            with tarfile.open(tar_path, 'r:gz') as tar:
                # 过滤危险路径和符号链接，防止路径遍历攻击
                safe_members = []
                for member in tar.getmembers():
                    if member.name.startswith('/') or '..' in member.name:
                        continue
                    if member.issym() or member.islnk():
                        continue
                    safe_members.append(member)
                tar.extractall(path=temp_dir, members=safe_members)
            print(f"源码已提取到: {temp_dir}")
            return True
        else:
            print(f"下载失败: HTTP {status}")
            return False
    except Exception as e:
        logger.error("下载源码包失败: %s", e)
        return False


def find_figures_from_source(temp_dir):
    """从源码目录中查找图片（搜索所有匹配的目录）"""
    figures = []
    seen_files = set()

    figure_dirs = ['pics', 'figures', 'fig', 'images', 'img']

    for fig_dir in figure_dirs:
        fig_path = os.path.join(temp_dir, fig_dir)
        if os.path.exists(fig_path):
            print(f"找到图片目录: {fig_path}")
            for filename in os.listdir(fig_path):
                file_path = os.path.join(fig_path, filename)
                if os.path.isfile(file_path) and filename not in seen_files:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg']:
                        seen_files.add(filename)
                        figures.append({
                            'type': 'source',
                            'source': 'arxiv-source',
                            'path': file_path,
                            'filename': filename
                        })

    # 如果没有找到单独的目录，检查根目录的图片文件
    if not figures:
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg'] and 'logo' not in filename.lower() and 'icon' not in filename.lower():
                    figures.append({
                        'type': 'source',
                        'source': 'arxiv-source',
                        'path': file_path,
                        'filename': filename
                    })

    return figures


def extract_pdf_figures(pdf_path, output_dir):
    """从PDF中提取图片（备选方案）"""
    print("从PDF直接提取图片（备选方案）...")

    try:
        pdf_doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error("无法打开PDF文件: %s (%s)", pdf_path, e)
        return []

    image_list = []

    try:
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            image_list_page = page.get_images(full=True)

            if image_list_page:
                for img_index, img in enumerate(image_list_page):
                    xref = img[0]
                    try:
                        base_image = pdf_doc.extract_image(xref)
                    except Exception as e:
                        logger.warning("  跳过无法提取的图片 (page %d, xref %d): %s", page_num + 1, xref, e)
                        continue

                    if base_image:
                        image_bytes = base_image['image']
                        image_ext = base_image['ext']

                        filename = f'page{page_num + 1}_fig{img_index + 1}.{image_ext}'
                        filepath = os.path.join(output_dir, filename)

                        with open(filepath, 'wb') as img_file:
                            img_file.write(image_bytes)

                        image_list.append({
                            'page': page_num + 1,
                            'index': img_index + 1,
                            'filename': filename,
                            'path': f'images/{filename}',
                            'size': len(image_bytes),
                            'ext': image_ext
                        })
    finally:
        pdf_doc.close()

    return image_list


def extract_from_pdf_figures(figures_pdf, output_dir):
    """从PDF格式图片文件中提取图片"""
    print(f"从PDF图片文件提取: {os.path.basename(figures_pdf)}")

    extracted = []
    doc = fitz.open(figures_pdf)
    filename = os.path.splitext(os.path.basename(figures_pdf))[0]

    try:
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            output_name = f'{filename}_page{i+1}.png'
            output_path = os.path.join(output_dir, output_name)
            pix.save(output_path)

            extracted.append({
                'filename': output_name,
                'path': f'images/{output_name}',
                'size': os.path.getsize(output_path),  # 使用实际文件大小
                'ext': 'png'
            })
    finally:
        doc.close()

    return extracted


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    if len(sys.argv) < 4:
        print("Usage: python extract_images.py <paper_id> <output_dir> <index_file>")
        print("  paper_id: arXiv ID (如: 2510.24701) 或本地PDF路径")
        print("  output_dir: 输出目录")
        print("  index_file: 索引文件路径")
        sys.exit(1)

    paper_input = sys.argv[1]
    output_dir = sys.argv[2]
    index_file = sys.argv[3]

    os.makedirs(output_dir, exist_ok=True)

    is_pdf_file = os.path.isfile(paper_input)
    arxiv_id = None
    pdf_path = None

    if is_pdf_file:
        pdf_path = paper_input
        filename = os.path.basename(pdf_path)
        match = re.search(r'(\d{4}\.\d+)', filename)
        if match:
            arxiv_id = match.group(1)
            print(f"检测到arXiv ID: {arxiv_id}")
    else:
        arxiv_id = paper_input

    with tempfile.TemporaryDirectory() as temp_dir:
        all_figures = []

        # 步骤1: 尝试从arXiv源码包提取
        if arxiv_id:
            if extract_arxiv_source(arxiv_id, temp_dir):
                source_figures = find_figures_from_source(temp_dir)
                if source_figures:
                    print(f"\n从arXiv源码找到 {len(source_figures)} 个图片文件")
                    for fig in source_figures:
                        output_file = os.path.join(output_dir, fig['filename'])
                        shutil.copy2(fig['path'], output_file)

                        all_figures.append({
                            'filename': fig['filename'],
                            'path': f'images/{fig["filename"]}',
                            'size': os.path.getsize(output_file),
                            'ext': os.path.splitext(fig['filename'])[1][1:].lower(),
                            'source': fig['source']
                        })
                        print(f"  - {fig['filename']}")

        # 步骤2: 如果源码包中没有找到足够的图片，从PDF中提取
        if len(all_figures) < 3 and pdf_path:
            print(f"\n找到的图片数量较少，从PDF直接提取...")
            pdf_figures = extract_pdf_figures(pdf_path, output_dir)
            for fig in pdf_figures:
                fig['source'] = 'pdf-extraction'
                all_figures.append(fig)

        # 步骤3: 检查源码包中的PDF图片文件并提取
        if arxiv_id and os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.pdf') and 'logo' not in file.lower() and file != f'{arxiv_id}.tar.gz':
                        pdf_fig_path = os.path.join(root, file)
                        try:
                            extracted = extract_from_pdf_figures(pdf_fig_path, output_dir)
                            for fig in extracted:
                                fig['source'] = 'pdf-figure'
                                all_figures.append(fig)
                        except Exception as e:
                            logger.warning("  跳过无法处理的PDF: %s (%s)", file, e)

    # 生成索引文件
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write('# 图片索引\n\n')
        f.write(f'总计：{len(all_figures)} 张图片\n\n')

        sources = {}
        for fig in all_figures:
            source = fig.get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(fig)

        for source, figs in sources.items():
            f.write(f'\n## 来源: {source}\n')
            for fig in figs:
                f.write(f'- 文件名：{fig["filename"]}\n')
                f.write(f'- 路径：{fig["path"]}\n')
                f.write(f'- 大小：{fig["size"] / 1024:.1f} KB\n')
                f.write(f'- 格式：{fig["ext"]}\n\n')

    print(f'\n成功提取 {len(all_figures)} 张图片')
    print(f'保存目录：{output_dir}')
    print(f'索引文件：{index_file}')
    print('\n图片列表：')
    for fig in all_figures:
        print(f'  - {fig["path"]} ({fig.get("source", "unknown")})')

    print('\nImage paths:')
    for fig in all_figures:
        print(fig["path"])


if __name__ == '__main__':
    main()
