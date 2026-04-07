# Doc Extractor

从Markdown文档中快速提取关键词相关信息的Python工具。

## 特性

- ✨ **一行代码调用** - 简单易用的API
- 🚀 **并行处理** - 多关键词并发提取
- 💾 **Redis缓存** - 自动存储，避免重复解析
- 🎯 **逐行匹配** - 精准定位相关内容
- 📊 **Top-K结果** - 返回最相关的N条结果

## 安装

```bash
pip install doc-extractor
```

或从源码安装：

```bash
git clone https://github.com/yourusername/doc-extractor.git
cd doc-extractor
pip install -r requirements.txt
pip install -e .
```

## 快速开始

### 方式1：一行代码调用

```python
import asyncio
from doc_extractor import extract_from_markdown

async def main():
    # 读取Markdown文件
    with open("report.md", "r", encoding="utf-8") as f:
        markdown_text = f.read()
    
    # 提取关键词信息
    results = await extract_from_markdown(
        markdown_text=markdown_text,
        keywords=["土壤", "环境", "位置"],
        top_k=10
    )
    
    # 输出结果
    for keyword, matches in results.items():
        print(f"\n【{keyword}】")
        for i, match in enumerate(matches, 1):
            print(f"{i}. {match}")

asyncio.run(main())
```

### 方式2：从文件直接提取

```python
from doc_extractor import extract_from_file

results = await extract_from_file(
    file_path="report.md",
    keywords=["土壤", "环境"]
)
```

### 方式3：使用类

```python
from doc_extractor import DocExtractor

extractor = DocExtractor(
    redis_host="localhost",
    redis_port=6379,
    top_k=10
)

results = await extractor.extract(markdown_text, keywords)
```

## 输出格式

```python
{
    "土壤": [
        "【土壤条件】\n土壤类型为红壤和黄壤...",
        "【土壤理化性质】\n土壤pH值5.5-6.5...",
        "【土壤环境】\n土壤质地以壤土为主..."
    ],
    "环境": [
        "【自然环境】\n项目区域属亚热带季风气候...",
        "【环境现状】\n地表水水质达到Ⅲ类标准..."
    ]
}
```

## API 文档

### `extract_from_markdown()`

```python
async def extract_from_markdown(
    markdown_text: str,
    keywords: List[str],
    llm_api_key: str = "",
    top_k: int = 10,
    **kwargs
) -> Dict[str, List[str]]
```

从Markdown文本提取关键词信息。

**参数：**
- `markdown_text`: Markdown格式文本
- `keywords`: 关键词列表
- `llm_api_key`: LLM API密钥（可选）
- `top_k`: 返回前K个结果（默认10）
- `**kwargs`: 其他参数传递给DocExtractor

**返回：**
```python
{
    "关键词1": [结果1, 结果2, ...],
    "关键词2": [结果1, 结果2, ...]
}
```

### `extract_from_file()`

```python
async def extract_from_file(
    file_path: str,
    keywords: List[str],
    llm_api_key: str = "",
    top_k: int = 10,
    **kwargs
) -> Dict[str, List[str]]
```

从Markdown文件提取关键词信息。

**参数：**
- `file_path`: Markdown文件路径
- `keywords`: 关键词列表
- `llm_api_key`: LLM API密钥（可选）
- `top_k`: 返回前K个结果（默认10）
- `**kwargs`: 其他参数传递给DocExtractor

### `DocExtractor`

核心提取器类。

```python
extractor = DocExtractor(
    redis_host="localhost",      # Redis地址
    redis_port=6379,              # Redis端口
    redis_db=0,                   # Redis数据库
    redis_password=None,          # Redis密码
    llm_api_key="",               # LLM API密钥
    llm_base_url="https://api.openai.com/v1",  # LLM API地址
    llm_model="gpt-4o-mini",      # 模型名称
    top_k=10                      # 返回结果数
)

# 提取
results = await extractor.extract(markdown_text, keywords)
```

## 依赖

- Python >= 3.8
- Redis >= 4.0.0
- openai >= 1.0.0

## 配置Redis

确保Redis服务已启动：

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo service redis-server start

# macOS
brew install redis
brew services start redis

# Windows
# 下载并安装 Redis for Windows
```

## 测试

```bash
# 运行测试
pytest

# 运行示例
python examples/example.py
```

## 示例

查看 `examples/` 目录下的完整示例：

- `example.py`: 基本用法
- `example_advanced.py`: 高级用法

