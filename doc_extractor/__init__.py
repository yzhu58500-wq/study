"""
文档信息提取模块

从Markdown文本中提取关键词相关信息，支持并行处理、Redis存储

Example:
    >>> from doc_extractor import extract_from_markdown
    >>> results = await extract_from_markdown(
    ...     markdown_text,
    ...     keywords=["土壤", "环境"],
    ...     top_k=10
    ... )
"""

from .extractor import DocExtractor, extract_from_markdown, extract_from_file

__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = ["DocExtractor", "extract_from_markdown", "extract_from_file"]
