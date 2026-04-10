# Simple RAG

一个开箱即用的简单 RAG (Retrieval-Augmented Generation) 系统，用于对 PDF 文档进行智能问答。

## 功能特性

- 📄 **PDF文档解析** - 支持从PDF文件中提取文本内容
- ✂️ **智能文本分块** - 支持自定义分块大小和重叠长度
- 🔍 **语义搜索** - 基于Embedding的语义相似度搜索
- 💬 **智能问答** - 基于上下文的AI问答生成
- ⚡ **Embedding缓存** - 自动缓存已计算的Embedding，避免重复API调用
- 🎛️ **灵活配置** - 支持命令行参数和环境变量配置
- 🔄 **交互模式** - 支持交互式多轮对话
- 🔐 **API密钥管理** - 通过.env文件安全管理API密钥

## 快速开始

### 1. 安装依赖

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
# 复制配置文件
cp .env.example .env

# 编辑.env文件，填入你的API密钥
```

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your-api-key-here
```

### 3. 准备测试数据

在项目根目录创建 `data` 文件夹，放入 PDF 文件：

```bash
mkdir -p data
# 将你的PDF文件放入 data/ 目录
```

### 4. 运行程序

**单次查询模式：**

```bash
python simple_rag.py --pdf data/document.pdf --query "文档的主要内容是什么？"
```

**交互式查询模式：**

```bash
python simple_rag.py --pdf data/document.pdf --interactive
```

## 命令行参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--pdf` | `-p` | str | 必需 | PDF文件路径 |
| `--query` | `-q` | str | - | 查询问题 |
| `--interactive` | `-i` | flag | False | 启动交互式模式 |
| `--chunk-size` | - | int | 1000 | 文本分块大小(字符数) |
| `--chunk-overlap` | - | int | 200 | 分块重叠大小(字符数) |
| `--top-k` | - | int | 5 | 返回的相关片段数量 |
| `--api-key` | - | str | - | OpenAI API密钥 |
| `--base-url` | - | str | OpenAI官方 | API基础URL |
| `--embedding-model` | - | str | text-embedding-ada-002 | Embedding模型 |
| `--chat-model` | - | str | gpt-4o | 聊天模型 |
| `--show-context` | - | flag | False | 显示参考上下文 |
| `--log-level` | - | str | INFO | 日志级别 |

## 使用示例

### 示例1：基础查询

```bash
python simple_rag.py --pdf data/document.pdf --query "文档的第三章讲了什么内容？"
```

输出：

```
================================================================================
问题: 文档的第三章讲了什么内容？
================================================================================

回答:
根据文档内容，第三章主要讲述了...

--------------------------------------------------------------------------------
参考来源: 5 个片段
```

### 示例2：显示上下文

```bash
python simple_rag.py --pdf data/document.pdf --query "什么是机器学习？" --show-context
```

输出会包含详细的上下文片段信息。

### 示例3：自定义参数

```bash
python simple_rag.py \
    --pdf data/document.pdf \
    --chunk-size 500 \
    --chunk-overlap 100 \
    --top-k 3 \
    --query "请总结文档的核心观点"
```

### 示例4：交互式模式

```bash
python simple_rag.py --pdf data/document.pdf --interactive
```

```
============================================================
Simple RAG 交互式查询模式
============================================================
提示: 输入 'quit' 或 'exit' 退出程序
============================================================

请输入您的问题: 文档的主要内容是什么？

============================================================
回答:
文档主要介绍了...

------------------------------------------------------------
(参考来源: 5 个片段)

请输入您的问题: quit
感谢使用，再见！
```

## 环境变量配置

除了命令行参数，还可以通过 `.env` 文件或环境变量进行配置：

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 必需 |
| `OPENAI_BASE_URL` | API基础URL | https://api.openai.com/v1 |
| `EMBEDDING_MODEL` | Embedding模型 | text-embedding-ada-002 |
| `CHAT_MODEL` | 聊天模型 | gpt-4o |
| `CHUNK_SIZE` | 分块大小 | 1000 |
| `CHUNK_OVERLAP` | 重叠大小 | 200 |
| `TOP_K` | Top-K结果数 | 5 |
| `LOG_LEVEL` | 日志级别 | INFO |

## 目录结构

```
simple-rag/
├── simple_rag.py       # 主程序文件
├── .env.example       # 配置文件模板
├── requirements.txt   # Python依赖
├── README.md          # 项目文档
├── .cache/            # Embedding缓存目录（自动创建）
│   └── embeddings.json
└── data/              # PDF文档目录（需手动创建）
    └── *.pdf
```

## 工作原理

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  PDF文档    │───▶│  文本提取    │───▶│  文本分块   │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   答案生成   │◀───│   RAG组合    │◀───│  语义搜索    │
└─────────────┘    └──────────────┘    └─────────────┘
                           │                   ▲
                           │                   │
                    ┌──────┴──────┐           │
                    │  用户问题    │───────────┘
                    └─────────────┘
```

1. **文本提取**：从PDF文件中提取文本内容
2. **文本分块**：将长文本分割成较小的片段
3. **Embedding生成**：为每个文本块生成向量表示
4. **语义搜索**：将用户问题转换为向量，搜索最相关的文本块
5. **答案生成**：将相关文本块作为上下文，让LLM生成答案

## API兼容性

本系统支持任何兼容OpenAI API格式的服务，包括：

- OpenAI 官方API
- Azure OpenAI Service
- 本地部署的模型（如 Ollama、LM Studio）
- 其他OpenAI兼容API（如 vLLM、FastChat 等）

配置示例：

```bash
# 使用本地Ollama服务
python simple_rag.py --pdf data/doc.pdf --query "问题" \
    --base-url http://localhost:11434/v1 \
    --api-key ollama \
    --embedding-model nomic-embed-text \
    --chat-model llama3
```

## 注意事项

1. **API费用**：Embedding和Chat API会产生费用，请注意控制调用频率
2. **PDF格式**：本系统仅支持文本型PDF，扫描版PDF需要先进行OCR处理
3. **缓存清理**：如需重新生成所有Embedding，删除 `.cache/embeddings.json` 文件
4. **中文支持**：系统支持中文PDF和中文问答，建议使用支持中文的模型

## 常见问题

### Q: 提示 "API密钥未配置"？

请确保已创建 `.env` 文件并正确配置 `OPENAI_API_KEY`。

### Q: 如何处理大型PDF？

可以通过调整 `--chunk-size` 参数来优化内存使用，建议大型PDF使用较小的分块大小。

### Q: Embedding缓存不生效？

检查 `.cache` 目录是否有写入权限，或手动删除缓存文件后重试。

### Q: 如何使用其他Embedding模型？

可以通过 `--embedding-model` 参数指定，或在 `.env` 中设置 `EMBEDDING_MODEL`。
