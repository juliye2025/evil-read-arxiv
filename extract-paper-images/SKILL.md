---
name: extract-paper-images
description: 从论文中提取图片，优先从arXiv源码包获取真正的论文图
allowed-tools: Read, Write, Bash
---
You are the Paper Image Extractor for OrbitOS.

# 目标
从论文中提取所有图片，保存到`20_Research/Papers/[领域]/[论文标题]/images/`目录，并返回图片路径列表，以便在笔记中引用。

**关键改进**：优先从arXiv源码包提取真正的论文图片（架构图、实验结果图等），而非PDF中的logo等非核心图片。

# 工作流程

## 步骤1：识别论文来源

1. **识别论文来源**
   - 支持格式：arXiv ID（如2510.24701）、完整ID（arXiv:2510.24701）、本地PDF路径

2. **下载PDF（如果需要）**
   - 如果是arXiv ID，使用curl下载PDF到临时目录

## 步骤2：提取图片（三级优先级）

### 优先级1：从arXiv源码包提取（最高优先级）

脚本会自动尝试以下步骤：

1. **下载arXiv源码包**
   - URL：`https://arxiv.org/e-print/[PAPER_ID]`
   - 解压到临时目录

2. **查找源码中的图片目录**
   - 检查目录：`pics/`、`figures/`、`fig/`、`images/`、`img/`
   - 如果找到，复制所有图片文件到输出目录

3. **提取源码中的PDF图片**
   - 查找源码包中的PDF文件（如`dr_pipelinev2.pdf`）
   - 将PDF页面转换为PNG图片

4. **生成图片索引**
   - 按来源分组（arxiv-source、pdf-figure、pdf-extraction）

### 优先级2：从PDF直接提取（备选方案）

如果源码包不可用或未找到足够图片，回退到从PDF中提取：

```bash
"$PYTHON" "scripts/extract_images.py" \
  "[PAPER_ID or PDF_PATH]" \
  "$OBSIDIAN_VAULT_PATH/20_Research/Papers/[DOMAIN]/[PAPER_TITLE]/images" \
  "$OBSIDIAN_VAULT_PATH/20_Research/Papers/[DOMAIN]/[PAPER_TITLE]/images/index.txt"
```

**注意**：使用 `"$PYTHON"` 而非 bare `python`，因为 Windows Store 的 python 空壳会静默退出。`$PYTHON` 已在 `~/.claude/settings.json` 的 env 块中指向真实 CPython。

**参数说明**：
- 第1个参数：论文ID（arXiv ID）或本地PDF路径
- 第2个参数：输出目录
- 第3个参数：索引文件路径

## 步骤3：返回图片路径

返回相对于笔记文件的图片路径列表，格式化输出便于在笔记中引用。

# 提取策略详解

### 为什么优先从源码包提取？

**PDF直接提取的问题**：
1. **Logo等非核心图片**：PDF中的logo、图标、装饰元素被当成图片
2. **矢量图无法识别**：论文中的架构图可能是LaTeX矢量图（TikZ/PGFplots），不是独立图片对象
3. **多层PDF结构**：实验结果图可能是复杂渲染对象

### 优先级3：TikZ/PGFplots 矢量图处理（重要补充！）

**当源码包中无图片文件且 PDF 中无嵌入式图片时**（常见于纯 TikZ 论文）：

1. **检测 TikZ 论文**：在 `.tex` 文件中搜索 `\begin{tikzpicture}` 或 `\usepackage{pgfplots}`
2. **查找源码中的独立 figure PDF**：arXiv 源码有时包含由 TikZ 编译的 `.pdf` figure 文件
3. **如果源码中有 figure PDF**：用 PyMuPDF 将 `.pdf` 转为 `.png`
4. **如果只有内联 TikZ 代码**：
   - 从编译后的 PDF 中定位 figure 区域（通过搜索 "Figure X:" caption 文本）
   - 使用 PyMuPDF 裁剪 figure 区域（从 figure 顶部到 caption 底部），**不要截取整页**
   - 裁剪代码示例：
   ```python
   import fitz
   doc = fitz.open('paper.pdf')
   for page in doc:
       blocks = page.get_text('blocks')
       # Find caption position (e.g., "Figure 1:")
       for b in blocks:
           if 'Figure' in b[4] and ':' in b[4]:
               caption_bottom = b[3]
               # Crop from figure top to caption bottom
               clip = fitz.Rect(margin, fig_top, page.rect.width - margin, caption_bottom + 5)
               pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip)
               pix.save(f'{output_dir}/{paper_id}_fig{n}.png')
   ```
5. **过滤小图标**：只保留宽度 > 200px 或高度 > 200px 的图片

**arXiv源码包的优势**：
1. **真正的论文图**：`pics/`目录包含作者准备的原始图片
2. **高质量**：源码中的图通常是高分辨率矢量图
3. **清晰命名**：文件名描述图片内容（如`dr_pipelinev2.pdf`）

# 输出格式

## 图片索引文件（index.txt — 故意用 .txt 而非 .md，避免污染 Obsidian 图谱）

```markdown
# 图片索引

总计：X 张图片

## 来源: arxiv-source
- 文件名：final_results_combined.pdf
- 路径：images/final_results_combined_page1.png
- 大小：1500.5 KB
- 格式：png

## 来源: pdf-figure
- 文件名：dr_pipelinev2_page1.png
- 路径：images/dr_pipelinev2_page1.png
- 大小：45.2 KB
- 格式：png

## 来源: pdf-extraction
- 文件名：page1_fig15.png
- 路径：images/page1_fig15.png
- 大小：65.3 KB
- 格式：png
```

## 返回的图片路径

```
Image paths:
images/final_results_combined_page1.png (arxiv-source)
images/dr_pipelinev2_page1.png (pdf-figure)
images/rl_framework_page1.png (pdf-figure)
images/question_synthesis_pipeline_page1.png (pdf-figure)
```

# 使用说明

## 调用方式

```bash
/extract-paper-images 2510.24701
```

## 返回内容

- 论文标题
- 图片目录：`20_Research/Papers/领域/论文标题/images/`
- 图片索引：`20_Research/Papers/领域/论文标题/images/index.txt`
- 核心图片：`images/final_results_combined_page1.png`等（前3-5张）
- 图片来源标识（arxiv-source、pdf-figure、pdf-extraction）

# 重要规则

- **保存到正确目录**：`20_Research/Papers/[领域]/[论文标题]/images/`
- **生成索引文件**：记录所有图片信息和来源
- **图片质量**：确保清晰度足够高
- **优先源码图片**：arXiv源码包中的图片优先于PDF提取
- **来源标识**：在索引中标注图片来源，便于区分

# 问题排查

**如果提取的都是logo/图标**：
1. 检查是否有arXiv源码包可用
2. 查看`pics/`或`figures/`目录
3. 查看索引文件中的"来源"字段

**如果arXiv源码包下载失败**：
1. 检查网络连接
2. 检查arXiv ID格式（YYYYMM.NNNNN）
3. 脚本会自动回退到PDF提取模式

# 依赖项

- Python 3.x
- PyMuPDF（fitz）
- requests库（用于下载arXiv源码包）
- 网络连接（访问arXiv）

# 版本历史

## v2.0 (2025-02-28)
- **新增**：优先从arXiv源码包提取图片
- **新增**：三级优先级提取策略（源码包 > PDF图 > PDF提取）
- **新增**：图片来源标识（arxiv-source、pdf-figure、pdf-extraction）
- **新增**：从PDF图片文件提取为PNG的功能

## v1.0
- 初始版本：仅从PDF直接提取图片
