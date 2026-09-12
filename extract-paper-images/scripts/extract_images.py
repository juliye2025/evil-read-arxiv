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
import hashlib
import os
import json
import sys
import re
import shutil
import tarfile
import tempfile
import logging
from pathlib import Path
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)
MARKDOWN_URL_RE = re.compile(r'\[[^\]]*\]\((https?://[^\s)]+)\)', re.IGNORECASE)
PLAIN_URL_RE = re.compile(r'https?://[^\s<>\[\]()]+', re.IGNORECASE)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False
    logger.warning("requests not found, using urllib")


def extract_source_reference(value):
    """接受纯 URL、尖括号 URL 或聊天中常见的 Markdown 链接。"""
    value = value.strip()
    markdown_urls = MARKDOWN_URL_RE.findall(value)
    if markdown_urls:
        return markdown_urls[-1].rstrip('.,;!?')
    if value.startswith('<') and value.endswith('>'):
        value = value[1:-1].strip()
    plain_urls = PLAIN_URL_RE.findall(value)
    if plain_urls and (len(plain_urls) == 1 or any(char.isspace() for char in value)):
        return plain_urls[-1].rstrip('.,;!?')
    return value


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


def normalize_arxiv_id(value):
    """仅识别合法 ID 或明确的 arxiv.org 链接，避免把普通 URL 中的数字误判为 arXiv。"""
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme in ('http', 'https'):
        host = (parsed.hostname or '').lower()
        if host not in ('arxiv.org', 'www.arxiv.org', 'export.arxiv.org'):
            return None
        candidate = unquote(parsed.path).strip('/')
        candidate = re.sub(r'^(abs|pdf|html|e-print)/', '', candidate, flags=re.IGNORECASE)
        candidate = re.sub(r'\.pdf$', '', candidate, flags=re.IGNORECASE)
    else:
        candidate = re.sub(r'^arxiv:\s*', '', value, flags=re.IGNORECASE).strip()

    match = re.fullmatch(r'(\d{4}\.\d{4,5})(v\d+)?', candidate, flags=re.IGNORECASE)
    if not match:
        return None
    paper_id = match.group(1)
    if not 1 <= int(paper_id[2:4]) <= 12:
        return None
    return paper_id + (match.group(2) or '').lower()


def is_http_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


def download_public_pdf(pdf_url, temp_dir, max_bytes=200 * 1024 * 1024):
    """下载公开 PDF URL，验证 PDF magic bytes，并限制文件大小。"""
    parsed = urlparse(pdf_url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError('仅支持公开 HTTP(S) PDF URL')
    filename = os.path.basename(unquote(parsed.path)) or 'document.pdf'
    filename = re.sub(r'[^\w.-]+', '_', filename).strip('._') or 'document.pdf'
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    pdf_path = os.path.join(temp_dir, filename)
    print(f"正在下载公开PDF: {pdf_url}")

    try:
        if HAS_REQUESTS:
            with requests.get(
                pdf_url,
                stream=True,
                timeout=(15, 90),
                allow_redirects=True,
                headers={'User-Agent': 'evil-read-arxiv/3.0'},
            ) as response:
                response.raise_for_status()
                total = 0
                first = b''
                with open(pdf_path, 'wb') as handle:
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        if not first:
                            first = chunk
                        total += len(chunk)
                        if total > max_bytes:
                            raise ValueError(f'PDF超过大小限制: {max_bytes} bytes')
                        handle.write(chunk)
                content_type = response.headers.get('Content-Type', '').split(';', 1)[0].lower()
                if not first.startswith(b'%PDF-'):
                    os.remove(pdf_path)
                    raise ValueError(f'URL返回的不是PDF (Content-Type: {content_type or "--"})')
        else:
            req = urllib.request.urlopen(pdf_url, timeout=90)
            content = req.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise ValueError(f'PDF超过大小限制: {max_bytes} bytes')
            if not content.startswith(b'%PDF-'):
                raise ValueError('URL返回的不是PDF')
            with open(pdf_path, 'wb') as handle:
                handle.write(content)
        print(f"PDF已下载: {pdf_path}")
        return pdf_path
    except Exception as e:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        logger.error("下载PDF失败: %s", e)
        return None


def download_arxiv_pdf(arxiv_id, temp_dir):
    """下载 arXiv PDF，供源码图片不足时回退提取。"""
    return download_public_pdf(f"https://arxiv.org/pdf/{arxiv_id}", temp_dir)


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

    # 如果没有找到单独的目录，检查根目录的图片文件。arXiv 源码
    # 经常把单页矢量图直接放在根目录，而主论文 PDF 是多页文档。
    if not figures:
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                lowered = filename.lower()
                is_candidate = ext in ['.png', '.jpg', '.jpeg']
                if ext == '.pdf':
                    try:
                        with fitz.open(file_path) as candidate_pdf:
                            is_candidate = candidate_pdf.page_count == 1
                    except Exception:
                        is_candidate = False
                if is_candidate and 'logo' not in lowered and 'icon' not in lowered:
                    figures.append({
                        'type': 'source',
                        'source': 'arxiv-source',
                        'path': file_path,
                        'filename': filename
                    })

    return figures


def extract_pdf_figures(
    pdf_path,
    output_dir,
    min_width=200,
    min_height=200,
    min_bytes=5000,
):
    """从PDF中提取图片（备选方案）

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        min_width: 最小宽度（像素），过滤图标/logo
        min_height: 最小高度（像素），过滤图标/logo
        min_bytes: 最小文件大小（字节），过滤小碎片
    """
    print("从PDF直接提取图片（备选方案）...")

    try:
        pdf_doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error("无法打开PDF文件: %s (%s)", pdf_path, e)
        return []

    candidates = []
    skipped = 0
    seen_xrefs = set()
    seen_hashes = set()

    try:
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            image_list_page = page.get_images(full=True)

            if image_list_page:
                for img_index, img in enumerate(image_list_page):
                    xref = img[0]
                    if xref in seen_xrefs:
                        skipped += 1
                        continue
                    seen_xrefs.add(xref)
                    try:
                        base_image = pdf_doc.extract_image(xref)
                    except Exception as e:
                        logger.warning("  跳过无法提取的图片 (page %d, xref %d): %s", page_num + 1, xref, e)
                        continue

                    if base_image:
                        image_bytes = base_image['image']
                        image_ext = base_image['ext']
                        img_width = base_image.get('width', 0)
                        img_height = base_image.get('height', 0)

                        # 过滤小图标、logo和UI碎片
                        if img_width < min_width or img_height < min_height:
                            skipped += 1
                            continue
                        if len(image_bytes) < min_bytes:
                            skipped += 1
                            continue

                        digest = hashlib.sha256(image_bytes).digest()
                        if digest in seen_hashes:
                            skipped += 1
                            continue
                        seen_hashes.add(digest)

                        filename = f'page{page_num + 1}_fig{img_index + 1}.{image_ext}'
                        candidates.append({
                            'page': page_num + 1,
                            'index': img_index + 1,
                            'filename': filename,
                            'path': f'images/{filename}',
                            'size': len(image_bytes),
                            'width': img_width,
                            'height': img_height,
                            'ext': image_ext,
                            '_bytes': image_bytes,
                            '_area': img_width * img_height,
                        })
    finally:
        pdf_doc.close()

    image_list = []
    for item in candidates:
        filepath = os.path.join(output_dir, item['filename'])
        with open(filepath, 'wb') as img_file:
            img_file.write(item.pop('_bytes'))
        item.pop('_area')
        image_list.append(item)

    if skipped:
        print(f"  已过滤 {skipped} 张完全重复或不满足原有尺寸阈值的图片")

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
        print("Usage: python extract_images.py <source> <output_dir> <index_file>")
        print("  source: arXiv ID/link、公开直接PDF URL 或本地PDF路径")
        print("  output_dir: 输出目录")
        print("  index_file: 索引文件路径")
        sys.exit(1)

    paper_input = extract_source_reference(sys.argv[1])
    output_dir = sys.argv[2]
    index_file = sys.argv[3]

    os.makedirs(output_dir, exist_ok=True)

    is_pdf_file = os.path.isfile(paper_input)
    input_url = paper_input if is_http_url(paper_input) else None
    arxiv_id = normalize_arxiv_id(paper_input)
    pdf_path = None

    if is_pdf_file:
        pdf_path = paper_input
        filename = os.path.basename(pdf_path)
        match = re.search(r'(\d{4}\.\d+)', filename)
        if match:
            detected = normalize_arxiv_id(match.group(1))
            if detected:
                arxiv_id = detected
                print(f"检测到arXiv ID: {arxiv_id}")
    elif not input_url and not arxiv_id:
        logger.error("无法识别输入。请提供合法 arXiv ID/link、公开直接 PDF URL 或本地 PDF。")
        sys.exit(2)

    with tempfile.TemporaryDirectory() as temp_dir:
        all_figures = []
        processed_source_pdfs = set()

        if input_url and not arxiv_id:
            pdf_path = download_public_pdf(input_url, temp_dir)
            if not pdf_path:
                logger.error("URL 未返回可用 PDF；若这是网页，请先用 paper-analyze 的来源解析器找到 PDF。")
                sys.exit(2)

        # 步骤1: 尝试从arXiv源码包提取
        if arxiv_id:
            if extract_arxiv_source(arxiv_id, temp_dir):
                source_figures = find_figures_from_source(temp_dir)
                if source_figures:
                    print(f"\n从arXiv源码找到 {len(source_figures)} 个图片文件")
                    for fig in source_figures:
                        extension = os.path.splitext(fig['filename'])[1].lower()
                        if extension == '.pdf':
                            processed_source_pdfs.add(os.path.realpath(fig['path']))
                            extracted = extract_from_pdf_figures(fig['path'], output_dir)
                            for converted in extracted:
                                converted['source'] = 'arxiv-source'
                                all_figures.append(converted)
                                print(f"  - {converted['filename']}")
                            continue

                        output_file = os.path.join(output_dir, fig['filename'])
                        shutil.copy2(fig['path'], output_file)
                        all_figures.append({
                            'filename': fig['filename'],
                            'path': f'images/{fig["filename"]}',
                            'size': os.path.getsize(output_file),
                            'ext': extension[1:],
                            'source': fig['source']
                        })
                        print(f"  - {fig['filename']}")

        # 步骤2: 如果源码包中没有找到足够的图片，下载/使用PDF并直接提取
        if len(all_figures) < 3 and not pdf_path and arxiv_id:
            pdf_path = download_arxiv_pdf(arxiv_id, temp_dir)

        if len(all_figures) < 3 and pdf_path:
            print(f"\n找到的图片数量较少，从PDF直接提取...")
            pdf_figures = extract_pdf_figures(pdf_path, output_dir)
            for fig in pdf_figures:
                fig['source'] = 'pdf-extraction'
                all_figures.append(fig)

        # arXiv 源码中的独立单页 PDF 常用于矢量插图。原实现会在这里
        # 连同刚下载的多页主论文 PDF 一起逐页转换，产生整页截图副本。
        # 继续支持任意目录中的单页 PDF 插图，但明确跳过主论文与已处理项。
        if arxiv_id and os.path.exists(temp_dir):
            main_pdf_path = os.path.realpath(pdf_path) if pdf_path else None
            for root, _dirs, files in os.walk(temp_dir):
                for file in files:
                    if not file.lower().endswith('.pdf') or 'logo' in file.lower():
                        continue
                    source_pdf = os.path.realpath(os.path.join(root, file))
                    if source_pdf == main_pdf_path or source_pdf in processed_source_pdfs:
                        continue
                    try:
                        with fitz.open(source_pdf) as candidate_pdf:
                            if candidate_pdf.page_count != 1:
                                continue
                        extracted = extract_from_pdf_figures(source_pdf, output_dir)
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
