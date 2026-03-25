---
name: start-my-day
description: 论文阅读工作流启动 - 生成今日论文推荐笔记 / Paper reading workflow starter - Generate daily paper recommendations
---

# Language Setting / 语言设置

This skill supports both Chinese and English reports. The language is determined by the `language` field in your config file:

- **Chinese (default)**: Set `language: "zh"` in config
- **English**: Set `language: "en"` in config

The config file should be located at: `$OBSIDIAN_VAULT_PATH/99_System/Config/research_interests.yaml`

## Language Detection

At the start of execution, read the config file to detect the language setting:

```bash
# Read language from config
LANGUAGE=$(grep -E "^\s*language:" "$OBSIDIAN_VAULT_PATH/99_System/Config/research_interests.yaml" | awk '{print $2}' | tr -d '"')

# Default to Chinese if not set
if [ -z "$LANGUAGE" ]; then
    LANGUAGE="zh"
fi
```

Then use this language setting throughout the workflow:
- When generating notes, pass `--language $LANGUAGE` to scripts
- Use appropriate section headers in the generated notes

---

You are the Daily Paper Workflow Starter for OrbitOS.

# 目标
帮助用户开启他们的研究日，搜索最近一个月和最近一年的极火、极热门、极优质论文，生成推荐笔记。

# 工作流程

## 工作流程概述

本 skill 使用 Python 脚本调用 arXiv API 搜索论文，解析 XML 结果并根据研究兴趣进行筛选和评分。

## 步骤1：收集上下文（静默）

1. **获取今日日期**
   - 确定当前日期（YYYY-MM-DD格式）

2. **读取研究配置**
   - 读取 `$OBSIDIAN_VAULT_PATH/99_System/Config/research_interests.yaml`（注意：文件名是 interests 不是 interest）获取研究领域
   - 提取：关键词、类别和优先级

3. **扫描现有笔记构建索引**
   - 扫描 `20_Research/Papers/` 目录下的所有 `.md` 文件
   - 提取笔记标题（从文件名和frontmatter的title字段）
   - 构建关键词到笔记路径的映射表，用于后续自动链接
   - 优先使用 frontmatter 中的 title 字段，其次使用文件名

## 步骤2：搜索论文

### 2.1 搜索范围

搜索所有相关分类的最近论文：

1. **搜索范围**
   - 使用 `scripts/search_arxiv.py` 搜索 arXiv
   - 查询：所有研究相关的 arXiv 分类
   - 按提交日期排序
   - 限制结果：200篇

2. **筛选策略**
   - 根据研究兴趣配置文件筛选论文
   - 计算综合推荐评分
   - 保留前10篇高评分论文

### 2.2 执行搜索和筛选

使用 `scripts/search_arxiv.py` 脚本完成搜索、解析和筛选：

```bash
# 使用 Python 脚本搜索、解析和筛选 arXiv 论文
# 首先切换到 skill 目录，然后执行脚本
cd "$SKILL_DIR"
python scripts/search_arxiv.py \
  --config "$OBSIDIAN_VAULT_PATH/99_System/Config/research_interests.yaml" \
  --output arxiv_filtered.json \
  --max-results 200 \
  --top-n 10 \
  --categories "cs.AI,cs.LG,cs.CL,cs.CV,cs.MM,cs.MA,cs.RO"
```

**脚本功能**：
1. **搜索 arXiv**
   - 调用 arXiv API 搜索指定分类的论文
   - 获取最多 200 篇最新论文

2. **解析 XML 结果**
   - 解析 API 返回的 XML
   - 提取：ID、标题、作者、摘要、发布日期、分类

3. **应用筛选和评分**
   - 根据研究兴趣配置文件筛选论文
   - 计算综合推荐评分（相关性40%、新近性20%、热门度30%、质量10%）
   - 按评分排序，保留前10篇

**输出**：
- `arxiv_filtered.json` - 筛选后的论文列表（JSON 格式）
- 每篇论文包含：
  - 论文ID、标题、作者、摘要
  - 发布日期、分类
  - 相关性评分、新近性评分、热门度评分、质量评分
  - 最终推荐评分、匹配的领域

## 步骤3：读取筛选结果

### 3.1 读取 JSON 结果

从 `arxiv_filtered.json` 中读取筛选和评分后的论文列表：

```bash
# 读取筛选结果
cat arxiv_filtered.json
```

**结果包含**：
- `total_found`: 搜索到的总论文数
- `total_filtered`: 筛选后的论文数
- `top_papers`: 前10篇高评分论文，每篇包含：
  - 论文ID、标题、作者、摘要
  - 发布日期、分类
  - 相关性评分、新近性评分、质量评分
  - 最终推荐评分、匹配的领域、匹配的关键词

### 3.2 评分说明

综合多个维度的评分：

```yaml
推荐评分 =
  相关性评分: 40%
  新近性评分: 20%
  热门度评分: 30%
  质量评分: 10%
```

**评分细则**：

1. **相关性评分** (40%)
   - 与研究兴趣的匹配程度
   - 标题关键词匹配：每个+0.5分
   - 摘要关键词匹配：每个+0.3分
   - 类别匹配：+1.0分
   - 最高分：~3.0

2. **新近性评分** (20%)
   - 最近30天内：+3分
   - 30-90天内：+2分
   - 90-180天内：+1分
   - 180天以上：0分

3. **热门度评分** (30%)
   - （如果数据可用）引用数 > 100：+3分
   - 引用数 50-100：+2分
   - 引用数 < 50：+1分
   - 无引用数据：0分
   - 或者基于发布后的时间推断（最近7天内的热门新论文）：+2分

4. **质量评分** (10%)
   - 从摘要推断：显著创新：+3分
   - 明确方法：+2分
   - 一般性工作：+1分
   - 或者读取已有笔记的质量评分

**最终推荐评分** = 相关性(40%) + 新近性(20%) + 热门度(30%) + 质量(10%)

## 步骤4：生成今日推荐笔记

### 4.1 读取筛选结果

从 `arxiv_filtered.json` 中读取筛选后的论文列表：
- 包含前 10 篇高评分论文
- 每篇论文包含完整信息：ID、标题、作者、摘要、评分、匹配领域

### 4.2 创建推荐笔记文件

1. **创建推荐笔记文件**
   - 文件名（根据语言设置）：
     - 中文（`language: "zh"`）：`10_Daily/YYYY-MM-DD论文推荐.md`
     - 英文（`language: "en"`）：`10_Daily/YYYY-MM-DD-paper-recommendations.md`
   - 使用变量：`10_Daily/YYYY-MM-DD${NOTE_SUFFIX}.md`（其中 `NOTE_SUFFIX` 在语言检测阶段已设置）
   - 必须包含属性：
     - `keywords`: 当天推荐论文的关键词（逗号分隔，从论文标题和摘要中提取）
     - `tags`: ["llm-generated", "daily-paper-recommend"]

2. **检查论文是否值得详细写**
   - **很值得读的论文**：推荐评分 >= 7.5 或特别推荐的论文
   - **一般推荐论文**：其他论文

3. **检查论文是否已有笔记**
   - 搜索 `20_Research/Papers/` 目录
   - 查找是否有该论文的详细笔记
   - 如果已有笔记：简略写，引用已有笔记
   - 如果无笔记：
     - 很值得读：在推荐笔记中写详细部分
     - 一般推荐：只写基本信息

### 4.2 推荐笔记结构

笔记文件结构如下：

```markdown
---
keywords: [关键词1, 关键词2, ...]
tags: ["llm-generated", "daily-paper-recommend"]
---

[具体论文推荐列表...]
```

#### 4.2.1 今日概览（放在论文列表之前）

在论文列表之前，添加一个"今日概览"部分，总结今日推荐论文的整体情况：

```markdown
## 今日概览

今日推荐的{论文数量}篇论文主要聚焦于**{主要研究方向1}**、**{主要研究方向2}**和**{主要研究方向3}**等前沿方向。

- **总体趋势**：{总结今日论文的整体研究趋势，如多模态模型推理能力、大模型高效推理优化等}

- **质量分布**：今日推荐的论文评分在 {最低分}-{最高分} 之间，{整体质量评价}。

- **研究热点**：
  - **{热点1}**：{简要描述}
  - **{热点2}**：{简要描述}
  - **{热点3}**：{简要描述}

- **阅读建议**：{给出阅读顺序建议，如建议先阅读某篇了解某方向，再关注某篇的方法等}
```

**说明**：
- 基于筛选出的前10篇论文的标题、摘要和评分进行总结
- 提取共同的研究主题和趋势
- 给出合理的阅读顺序建议

#### 4.2.2 所有论文统一格式

所有论文按评分从高到低排列，使用统一格式

**当 `language: "zh"` 时使用中文格式**：
```markdown
### [[论文名字]]
- **作者**：[作者列表]
- **机构**：[机构名称]
- **链接**：[arXiv](链接) | [PDF](链接)
- **来源**：[arXiv]
- **笔记**：[[已有笔记路径]] 或 —

**一句话总结**：[一句话概括论文的核心贡献]

**核心贡献/观点**：
- [贡献点1]
- [贡献点2]
- [贡献点3]

**关键结果**：[从摘要中提取的最重要结果]

---
```

**当 `language: "en"` 时使用英文格式**：
```markdown
### [[paper_note_filename|Paper Title]]
- **Authors**: [author list]
- **Affiliation**: [affiliation or "Not specified"]
- **Links**: [arXiv](link) | [PDF](link)
- **Source**: arXiv
- **Notes**: [[existing_note_path]] or —

**One-line Summary**: [one-line summary of core contribution]

**Core Contributions**:
- [Contribution 1]
- [Contribution 2]
- [Contribution 3]

**Key Results**: [most important results from abstract]

---
```

**说明**：
- 论文名称使用 wikilink 格式：`[[论文名字]]`
- 对于前三篇论文，论文名字会关联到详细报告
- 对于其他论文，论文名字可以作为wikilink占位符，方便以后创建笔记

#### 4.2.3 前三篇论文插入图片和调用详细分析

对于前3篇论文（评分最高的3篇）：

**步骤0：检查论文是否已有笔记**
```bash
# 在 20_Research/Papers/ 目录中搜索已有笔记
# 搜索方式：
# 1. 按论文ID搜索（如 2602.23351）
# 2. 按论文标题搜索（模糊匹配）
# 3. 按论文标题关键词搜索
```

**步骤1：根据检查结果决定处理方式**

如果已有笔记：
- 不生成新的详细报告
- 使用已有笔记路径作为 wikilink
- 在推荐笔记的"详细报告"字段引用已有笔记
- 检查是否需要提取图片（如果没有 images 目录或 images 目录为空）
  - 如果需要图片：调用 `extract-paper-images`
  - 如果已有图片：使用现有图片

如果没有笔记：
- 调用 `extract-paper-images` 提取图片
- 调用 `paper-analyze` 生成详细报告
- 在推荐笔记中添加图片和详细报告链接

**步骤2：在推荐笔记中插入图片和链接**

**当 `language: "zh"` 时（如果已有笔记）**：
```markdown
### [[已有论文名称]]
- **作者**：[作者列表]
- **机构**：[机构名称]
- **链接**：[arXiv](链接) | [PDF](链接)
- **来源**：[arXiv]
- **详细报告**：[[已有笔记路径]]
- **笔记**：已有详细分析

**一句话总结**：[一句话概括论文的核心贡献]

![现有图片|600](现有图片路径)

**核心贡献/观点**：
...
```

**当 `language: "zh"` 时（如果没有笔记）**：
```markdown
### [[论文名字]]
- **作者**：[作者列表]
- **机构**：[机构名称]
- **链接**：[arXiv](链接) | [PDF](链接)
- **来源**：[arXiv]
- **详细报告**：[[详细报告路径]] (自动生成)

**一句话总结**：[一句话概括论文的核心贡献]

![新提取的图片|600](新图片路径)

**核心贡献/观点**：
...
```

**当 `language: "en"` 时（如果已有笔记）**：
```markdown
### [[paper_note_filename|Paper Title]]
- **Authors**: [author list]
- **Affiliation**: [affiliation or "Not specified"]
- **Links**: [arXiv](link) | [PDF](link)
- **Source**: arXiv
- **Detailed Report**: [[existing_note_path]]
- **Notes**: Existing detailed analysis

**One-line Summary**: [one-line summary]

![existing image|600](existing_image_path)

**Core Contributions**:
...
```

**当 `language: "en"` 时（如果没有笔记）**：
```markdown
### [[paper_note_filename|Paper Title]]
- **Authors**: [author list]
- **Affiliation**: [affiliation or "Not specified"]
- **Links**: [arXiv](link) | [PDF](link)
- **Source**: arXiv
- **Detailed Report**: [[detailed_report_path]] (auto-generated)

**One-line Summary**: [one-line summary]

![new extracted image|600](new_image_path)

**Core Contributions**:
...
```

**图片说明**：
- 图片路径：`20_Research/Papers/[论文分类]/images/[论文ID]_fig1.png`
- 宽度设置为 600px
- 自动提取，无需手动操作
- **禁止 URL 编码**：Obsidian 的图片语法 `![alt|600](path)` 必须使用原始路径，**不得**对空格、`&` 等字符做 percent-encoding。
  - 正确：`![img|600](20_Research/Papers/Multimodal & Vision-Language/ThinkJEPA/images/arch_page1.png)`
  - 错误：`![img|600](20_Research/Papers/Multimodal%20%26%20Vision-Language/ThinkJEPA/images/arch_page1.png)`
  - 此规则同样适用于 wikilink 以外的所有 markdown 图片引用路径

**详细报告说明**：
- 报告路径：`20_Research/Papers/[论文分类]/[note_filename].md`
- **重要**：使用 JSON 中的 `note_filename` 字段（而非原始标题）拼接 wikilink，确保与 `generate_note.py` 创建的文件名一致
  - 正确：`[[20_Research/Papers/大模型/Hypothesis-Conditioned_Query_Rewriting_for_Decision-Useful_Retrieval]]`
  - 错误：`[[20_Research/Papers/大模型/Hypothesis-Conditioned Query Rewriting for Decision-Useful Retrieval]]`
- 在"详细报告"字段显示 wikilink：`- **详细报告**：[[20_Research/Papers/[domain]/[note_filename]]]`
- **论文分类（domain）命名规则**：domain 名称必须与 `paper-analyze` 实际创建的目录名完全一致，**不得截断**。例如：
  - 正确：`[[20_Research/Papers/Computational Pathology/ReconMIL_...]]`（保留完整域名）
  - 错误：`[[20_Research/Papers/Computational]]`（截断了 "Pathology" 部分）
  - 正确：`[[20_Research/Papers/Foundation Models & LLM/...]]`
  - 错误：`[[20_Research/Papers/Foundation]]`（截断了 "Models & LLM" 部分）
- 详细报告由 `paper-analyze` 自动生成，包含完整的论文分析

## 步骤5：自动链接关键词（可选）

在生成推荐笔记后，自动链接关键词到现有笔记：

```bash
# 步骤1：扫描现有笔记
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json

# 步骤2：生成推荐笔记（正常流程）
# ... 使用 search_arxiv.py 搜索论文 ...

# 步骤3：链接关键词（新增步骤）
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input "10_Daily/YYYY-MM-DD${NOTE_SUFFIX}.md" \
  --output "10_Daily/YYYY-MM-DD${NOTE_SUFFIX}_linked.md"
```

**注意**：
- 关键词链接脚本会自动跳过 frontmatter、标题行、代码块
- 过滤通用词（and, for, model, learning 等）
- 保留已有 wikilink 不被修改

# 重要规则

- **搜索范围扩大**：搜索近一个月 + 近一年热门论文
- **综合推荐评分**：结合相关性、新近性、热门度、质量四个维度
- **文件名以日期**：保持 `10_Daily/YYYY-MM-DD${NOTE_SUFFIX}.md` 格式（中文：`论文推荐`，英文：`paper-recommendations`）
- **添加今日概览**：在推荐笔记开头添加"## 今日概览"部分，总结今日论文的主要研究方向、总体趋势、质量分布、研究热点和阅读建议
- **按评分排序**：所有论文按推荐评分从高到低排列
- **前3篇特殊处理**：
  - 论文名称用 wikilink 格式：`[[论文名字]]`
  - 自动提取第一张图片并插入
  - 自动调用 `paper-analyze` 生成详细报告
  - 在"详细报告"字段显示 wikilink 关联
- **其他论文**：只写基本信息，不插入图片
- **保持快速**：让用户快速了解当日推荐
- **避免重复**：检查已推荐论文
- **自动关键词链接**：
  - 在生成推荐笔记后，自动扫描现有笔记
  - 将文本中的关键词（如 BLIP、CLIP 等）替换为 wikilink
  - 示例：`BLIP` → `[[BLIP]]`
  - 保留已有 wikilink 不被修改
  - 不替换代码块中的内容
  - 不替换已存在 wikilink 的内容（避免重复）

# 与其他 skills 的区别

## start-my-day (本skill)
- **目的**：从大范围搜索中筛选推荐论文，生成每日推荐笔记
- **搜索范围**：近一个月 + 近一年热门/优质论文
- **内容**：推荐列表
  - 开头包含"今日概览"：总结主要研究方向、总体趋势、质量分布、研究热点和阅读建议
  - 所有论文统一格式
  - 前3篇特殊处理：
    - 论文名称用 wikilink 格式：`[[论文名字]]`
    - 自动提取第一张图片并插入
    - 自动调用 `paper-analyze` 生成详细报告
    - 在"详细报告"字段显示 wikilink 关联
- **图片处理**：前3篇自动提取并插入第一张图片；不包含所有论文的图
- **详细报告**：前3篇自动生成，其他论文不生成
- **适用**：用户每天手动触发
- **笔记引用**：如果论文已有笔记，简略写并引用；如果分析需要引用历史笔记，也直接引用

## paper-analyze (深度分析skill)
- **目的**：用户主动查看单篇论文，深度研究
- **适用场景**：用户自己还想要看，但AI没有整理到的论文
- **内容**：详细的论文深度分析笔记
  - 包含所有核心信息：研究问题、方法概述、方法架构、关键创新、实验结果、深度分析、相关论文对比等
  - **图文并茂**：论文中的所有图片都要用上（核心架构图、方法图、实验结果图等）
- **适用**：用户主动调用 `/paper-analyze [论文ID]` 或论文标题
- **重要要求**：无论是start-my-day整理的论文，还是用户主动查看的论文，都要图文并茂

# 使用说明

当用户输入 "start my day" 时，按以下步骤执行：

**日期参数支持**：
- 无参数：生成当天的论文推荐笔记
- 有参数（YYYY-MM-DD）：生成指定日期的论文推荐笔记
  - 例如：`/start-my-day 2026-02-27`

## 自动执行流程

1. **获取目标日期**
   - 无参数：使用当前日期（YYYY-MM-DD格式）
   - 有参数：使用指定日期

2. **扫描现有笔记构建索引**
   ```bash
   # 扫描 vault 中现有的论文笔记
   cd "$SKILL_DIR"
   python scripts/scan_existing_notes.py \
     --vault "$OBSIDIAN_VAULT_PATH" \
     --output existing_notes_index.json
   ```
   - 扫描 `20_Research/Papers/` 目录
   - 提取笔记标题和 tags
   - 构建关键词到笔记路径的映射表

3. **搜索和筛选 arXiv 论文**
   ```bash
   # 使用 Python 脚本搜索、解析和筛选 arXiv 论文
   # 首先切换到 skill 目录，然后执行脚本
   # 如果有目标日期参数（如 2026-02-21），传递给 --target-date
   cd "$SKILL_DIR"
   python scripts/search_arxiv.py \
     --config "$OBSIDIAN_VAULT_PATH/99_System/Config/research_interests.yaml" \
     --output arxiv_filtered.json \
     --max-results 200 \
     --top-n 10 \
     --categories "cs.AI,cs.LG,cs.CL,cs.CV,cs.MM,cs.MA,cs.RO" \
     --target-date "{目标日期}"  # 如果用户指定了日期，替换为实际日期
   ```

4. **读取筛选结果**
   - 从 `arxiv_filtered.json` 中读取筛选结果
   - 获取前 10 篇高评分论文
   - 每篇论文包含：ID、标题、作者、摘要、评分、匹配领域

5. **生成推荐笔记（包含关键词链接）**
   - 创建 `10_Daily/YYYY-MM-DD${NOTE_SUFFIX}.md`（使用目标日期，`NOTE_SUFFIX` 依语言设置）
   - **按评分排序**：所有论文按推荐评分从高到低排列
   - **前3篇特殊处理**：
     - 论文名称用 wikilink 格式：`[[论文名字]]`
     - 在"一句话总结"后插入实际提取的第一张图片
     - 在"详细报告"字段显示 wikilink 关联
   - **其他论文**：只写基本信息，不插入图片
   - **关键词自动链接**（重要！）：
     - 在生成笔记后，扫描文本中的关键词
     - 使用 `existing_notes_index.json` 进行匹配
     - 将关键词替换为 wikilink，如 `BLIP` → `[[BLIP]]`
     - 保留已有 wikilink 不被修改
     - 不替换代码块中的内容

6. **对前三篇论文执行深度分析**
   ```bash
   # 对每篇前三论文执行以下操作

   # 步骤1：检查论文是否已有笔记
   # 在 20_Research/Papers/ 目录中搜索
   # - 按论文ID搜索（如 2602.23351）
   # - 按论文标题搜索（模糊匹配）
   # - 按论文标题关键词搜索（如 "Pragmatics", "Reporting Bias"）

   # 步骤2：根据检查结果决定处理方式
   if 已有笔记:
       # 不生成新的详细报告
       # 使用已有的笔记路径
       # 只提取图片（如果没有图片的话）
   else:
       # 提取第一张图片
       /extract-paper-images [论文ID]

       # 生成详细分析报告
       /paper-analyze [论文ID]
   ```
   - **如果已有笔记**：
     - 不重复生成详细报告
     - 使用已有笔记路径作为 wikilink
     - 检查是否需要提取图片（如果没有 images 目录或 images 目录为空）
     - 在推荐笔记的"详细报告"字段引用已有笔记
   - **如果没有笔记**：
     - 提取第一张图片并保存到 vault
     - 生成详细的论文分析报告
     - 在推荐笔记中添加图片和详细报告链接

## 临时文件清理

- 搜索过程产生的临时 XML 和 JSON 文件可以清理
- 推荐笔记已保存到 vault 后，临时文件不再需要

## 依赖项

- Python 3.x（用于运行搜索和筛选脚本）
- PyYAML（用于读取研究兴趣配置文件）
- 网络连接（访问 arXiv API）
- `20_Research/Papers/` 目录（用于扫描现有笔记和保存详细报告）
- `extract-paper-images` skill（用于提取论文图片）
- `paper-analyze` skill（用于生成详细报告）

## 脚本说明

### search_arxiv.py

位于 `scripts/search_arxiv.py`，功能包括：

1. **搜索 arXiv**：调用 arXiv API 获取论文
2. **解析 XML**：提取论文信息（ID、标题、作者、摘要等）
3. **筛选论文**：根据研究兴趣配置文件筛选
4. **计算评分**：综合相关性、新近性、质量等维度
5. **输出 JSON**：保存筛选后的结果到 `arxiv_filtered.json`

### scan_existing_notes.py

位于 `scripts/scan_existing_notes.py`，功能包括：

1. **扫描笔记目录**：扫描 `20_Research/Papers/` 下所有 `.md` 文件
2. **提取笔记信息**：
   - 文件路径
   - 文件名
   - frontmatter 中的 title 字段
   - tags 字段
3. **构建索引**：创建关键词到笔记路径的映射表
4. **输出 JSON**：保存索引到 `existing_notes_index.json`

**使用方法**：
```bash
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json
```

**输出格式**：
```json
{
  "notes": [
    {
      "path": "20_Research/Papers/多模态技术/BLIP_Bootstrapping-Language-Image-Pre-training.md",
      "filename": "BLIP_Bootstrapping-Language-Image-Pre-training.md",
      "title": "BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation",
      "title_keywords": ["BLIP", "Bootstrapping", "Language-Image", "Pre-training", "Unified", "Vision-Language", "Understanding", "Generation"],
      "tags": ["Vision-Language-Pre-training", "Multimodal-Encoder-Decoder", "Bootstrapping", "Image-Captioning", "Image-Text-Retrieval", "VQA"]
    }
  ],
  "keyword_to_notes": {
    "blip": ["20_Research/Papers/多模态技术/BLIP_Bootstrapping-Language-Image-Pre-training.md"],
    "bootstrapping": ["20_Research/Papers/多模态技术/BLIP_Bootstrapping-Language-Image-Pre-training.md"],
    "vision-language": ["20_Research/Papers/多模态技术/BLIP_Bootstrapping-Language-Image-Pre-training.md"]
  }
}
```

### link_keywords.py

位于 `scripts/link_keywords.py`，功能包括：

1. **读取文本**：读取需要处理的文本内容
2. **读取笔记索引**：从 `existing_notes_index.json` 加载笔记映射
3. **替换关键词**：在文本中查找关键词，替换为wikilink
   - 不替换已存在的 wikilink（如 `[[BLIP]]`）
   - 不替换代码块中的内容
   - 匹配规则：
     - 优先匹配完整的标题关键词
     - 其次匹配 tags 中的关键词
     - 匹配时忽略大小写
     - 过滤通用词（and, for, model, learning 等）
     - 跳过 frontmatter 和标题行
4. **输出结果**：输出处理后的文本

**使用方法**：
```bash
# 首先切换到 skill 目录，然后执行脚本
cd "$SKILL_DIR"
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input "input.txt" \
  --output "output.txt"
```

**匹配示例**：
```
原始文本：
"这篇论文使用了BLIP和CLIP作为基线方法。"

处理后：
"这篇论文使用了[[BLIP]]和[[CLIP]]作为基线方法。"
```

**使用方法**：
```bash
# 步骤1：扫描现有笔记
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json

# 步骤2：生成推荐笔记（正常流程）
# ... 使用 search_arxiv.py 搜索论文 ...

# 步骤3：链接关键词（新增步骤）
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input "10_Daily/YYYY-MM-DD${NOTE_SUFFIX}.md" \
  --output "10_Daily/YYYY-MM-DD${NOTE_SUFFIX}_linked.md"
```

**关键特性**：
- **智能匹配**：忽略大小写匹配中文环境
- **保护已有链接**：不替换已存在的wikilink
- **避免代码污染**：不替换代码块和行内代码中的内容
- **路径编码**：使用UTF-8编码确保中文路径正确
- **跳过敏感区域**：不处理 frontmatter、标题行、代码块

### 关键词链接实现（新增！）

**功能概述**：
在生成每日推荐笔记后，自动扫描现有笔记，将文本中的关键词（如BLIP、CLIP等）替换为wikilink（如[[BLIP]]）。

**实现流程**：
1. **扫描现有笔记**：扫描 `20_Research/Papers/` 目录
   - 提取笔记的frontmatter（title、tags）
   - 从标题中提取关键词（按分隔符和常见词缀）
   - 从tags中提取关键词（按连字符分割）
   - 构建关键词到笔记路径的映射表

2. **生成推荐笔记**：正常生成推荐笔记内容

3. **链接关键词**：处理生成的笔记
   - 找到文本中的关键词
   - 用wikilink替换找到的关键词
   - 保留已有wikilink
   - 不替换代码块和行内代码中的内容

**使用方法**：
```bash
# 步骤1：扫描现有笔记
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json

# 步骤2：生成推荐笔记（正常流程）
# ... 使用 search_arxiv.py 搜索论文 ...

# 步骤3：链接关键词（新增步骤）
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input "10_Daily/YYYY-MM-DD${NOTE_SUFFIX}.md" \
  --output "10_Daily/YYYY-MM-DD${NOTE_SUFFIX}_linked.md"
```

**关键特性**：
- **智能匹配**：忽略大小写匹配中文环境
- **保护已有链接**：不替换已存在的wikilink
- **避免代码污染**：不替换代码块和行内代码中的内容
- **路径编码**：使用UTF-8编码确保中文路径正确
