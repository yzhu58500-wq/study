# RAG系统 - Markdown切分模块

## 功能说明

本模块用于将Markdown文件按二级标题切分成chunks，方便后续加载到向量数据库。

### 核心功能
1. **按二级标题切分**：以二级标题为边界，每个chunk包含完整的二级标题及其内容
2. **表格处理**：自动识别并合并跨页/跨栏表格
3. **元数据提取**：记录一级标题、二级标题、编号、页码、是否含表格等信息
4. **Chunk大小控制**：支持设置最大和最小字符数限制

## 使用方法

### 方法1：一行代码调用（推荐）

```python
from rag_modules import chunk_markdown

# 基础用法：不限制大小
chunks = chunk_markdown("your_document.md")

# 限制最大字符数为1000
chunks = chunk_markdown("your_document.md", max_chunk_size=1000)

# 限制最小字符数为100，最大为1000
chunks = chunk_markdown("your_document.md", max_chunk_size=1000, min_chunk_size=100)

# 访问chunk信息
for chunk in chunks:
    print(f"标题: {chunk.level_2_title}")
    print(f"内容长度: {len(chunk.content)}")
    print(f"一级标题: {chunk.level_1_title}")
    print(f"包含表格: {chunk.has_table}")
```

### 方法2：使用类接口（可配置）

```python
from rag_modules import MarkdownChunker

# 创建解析器
chunker = MarkdownChunker(
    table_merge_threshold=23.0,
    max_chunk_size=1000,  # 最大1000字符
    min_chunk_size=100    # 最小100字符
)

# 处理文件
chunks = chunker.process_file("your_document.md", merge_tables=True)

# 保存结果
chunker.save_chunks(chunks, "output.txt", format='txt')
chunker.save_chunks(chunks, "output.json", format='json')
```

## Chunk大小控制逻辑

### 最大值限制（max_chunk_size）
当一个chunk超过最大字符数时：
1. **优先按段落拆分**：尝试在段落边界处切分
2. **按句子拆分**：如果单个段落过大，按句子切分
3. **保留元数据**：拆分后的chunks会标记原chunk ID和部分编号

### 最小值限制（min_chunk_size）
当一个chunk低于最小字符数时：
1. **尝试合并**：如果前一个chunk属于同一级标题，自动合并
2. **保留标记**：无法合并的过小chunks会在metadata中标记`small_chunk=True`

## Chunk数据结构

```python
@dataclass
class Chunk:
    chunk_id: int              # Chunk编号
    content: str               # 内容文本
    level_1_title: str         # 所属一级标题
    level_2_title: str         # 二级标题（本chunk标题）
    level_1_index: int         # 一级标题编号
    level_2_index: int         # 二级标题编号
    page_numbers: List[int]    # 所在页码
    has_table: bool            # 是否包含表格
    metadata: Dict             # 其他元数据
```

### metadata字段说明
- `split_from`: 标记该chunk是从哪个chunk拆分而来
- `part`: 标记是第几部分
- `merged_from`: 标记该chunk由哪些chunks合并而来
- `small_chunk`: 标记该chunk过小且无法合并

## 测试方法

### 运行测试
```bash
# 基础测试（不限制大小）
python test_markdown_chunker.py ./your_file.md

# 限制最大字符数
python test_markdown_chunker.py ./your_file.md 1000

# 限制最小和最大字符数
python test_markdown_chunker.py ./your_file.md 1000 100
```

### 查看结果
测试脚本会生成两个文件：
- `your_file_chunks.txt`: 文本格式，方便人工查看
- `your_file_chunks.json`: JSON格式，便于程序处理

## 输出示例

### TXT格式
```
============================================================
Chunk ID: 0
一级标题: 第一章 引言
二级标题: 1.1 研究背景
标题编号: L1-1, L2-1
页码: [1, 2]
包含表格: False
字符数: 856
============================================================

## 1.1 研究背景

本章节介绍研究背景...
```

### JSON格式
```json
[
  {
    "chunk_id": 0,
    "content": "## 1.1 研究背景\n\n本章节介绍...",
    "level_1_title": "第一章 引言",
    "level_2_title": "1.1 研究背景",
    "level_1_index": 1,
    "level_2_index": 1,
    "page_numbers": [1, 2],
    "has_table": false,
    "metadata": {}
  }
]
```

## 表格合并规则

模块会自动识别并处理以下情况的表格：

1. **跨栏表格**：同一页且表头表题相同 → 自动合并
2. **跨页表格**：跨一页且无中间字符 + 距离 < 阈值 → 自动合并
3. **跨两页表格**：保持独立

## 使用建议

### 推荐的chunk大小
- **小文档**：max_chunk_size=500-1000
- **中等文档**：max_chunk_size=1000-2000
- **大文档**：max_chunk_size=2000-4000

### 注意事项
1. Markdown文件需包含清晰的一级（#）和二级（##）标题
2. 表格需使用标准Markdown格式（| 和 ---）
3. 页码信息需通过注释标记（如 `<!-- Page 1 -->`）
4. 设置过小的max_chunk_size可能导致语义被切断
5. 设置过大的min_chunk_size可能导致过多chunks被合并

## 下一步

此模块为RAG系统的第一步，后续模块：
- 向量化和存储（Milvus）
- 检索模块
- 生成模块
