#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple RAG (Retrieval-Augmented Generation) System
简单RAG系统 - 开箱即用的文档问答工具

功能特性：
- 支持PDF文档解析和文本分块
- 支持自定义embedding模型和生成模型
- 支持本地embedding缓存，避免重复调用API
- 支持命令行参数配置
- 支持交互式查询模式

版本：1.0.0
"""

import os
import sys
import json
import hashlib
import argparse
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from functools import lru_cache

import numpy as np
import fitz  # PyMuPDF
from openai import OpenAI, APIError, AuthenticationError, RateLimitError
from dotenv import load_dotenv

# ============================================================================
# 配置管理
# ============================================================================

@dataclass
class RAGConfig:
    """RAG系统配置类"""
    # API配置
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-ada-002"
    chat_model: str = "gpt-4o"
    
    # 文本处理配置
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    
    # 系统配置
    cache_dir: str = ".cache"
    embedding_cache_file: str = ".cache/embeddings.json"
    log_level: str = "INFO"
    
    def __post_init__(self):
        """初始化后处理"""
        # 从环境变量加载API配置
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = self.base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # 使用环境变量覆盖其他配置
        if os.getenv("EMBEDDING_MODEL"):
            self.embedding_model = os.getenv("EMBEDDING_MODEL")
        if os.getenv("CHAT_MODEL"):
            self.chat_model = os.getenv("CHAT_MODEL")
        if os.getenv("CHUNK_SIZE"):
            self.chunk_size = int(os.getenv("CHUNK_SIZE"))
        if os.getenv("CHUNK_OVERLAP"):
            self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP"))
        if os.getenv("TOP_K"):
            self.top_k = int(os.getenv("TOP_K"))
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 验证必需配置
        if not self.api_key:
            raise ValueError("API密钥未配置！请设置OPENAI_API_KEY环境变量或创建.env文件")
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size必须大于0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap不能为负数")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap必须小于chunk_size")
        if self.top_k <= 0:
            raise ValueError("top_k必须大于0")
        return True


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    配置日志系统
    
    Args:
        level: 日志级别
        
    Returns:
        Logger: 配置好的日志记录器
    """
    logger = logging.getLogger("simple_rag")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# ============================================================================
# 工具函数
# ============================================================================

def compute_text_hash(text: str) -> str:
    """
    计算文本的MD5哈希值，用于生成缓存键
    
    Args:
        text: 输入文本
        
    Returns:
        str: MD5哈希值
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def save_json(data: Any, filepath: str) -> None:
    """
    保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        filepath: 文件路径
    """
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Any:
    """
    从JSON文件加载数据
    
    Args:
        filepath: 文件路径
        
    Returns:
        加载的数据
    """
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# PDF处理模块
# ============================================================================

def extract_text_from_pdf(pdf_path: str, logger: Optional[logging.Logger] = None) -> str:
    """
    从PDF文件中提取文本
    
    Args:
        pdf_path: PDF文件的路径
        logger: 日志记录器
        
    Returns:
        str: 从PDF中提取的文本
        
    Raises:
        FileNotFoundError: PDF文件不存在
        ValueError: PDF文件为空或无法读取
    """
    logger = logger or setup_logging()
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    
    try:
        logger.info(f"正在打开PDF文件: {pdf_path}")
        mypdf = fitz.open(pdf_path)
        
        if mypdf.page_count == 0:
            raise ValueError("PDF文件为空，没有页面")
        
        logger.info(f"PDF文件共有 {mypdf.page_count} 页")
        
        all_text = []
        for page_num in range(mypdf.page_count):
            page = mypdf[page_num]
            text = page.get_text("text")
            if text.strip():
                all_text.append(text)
        
        mypdf.close()
        
        full_text = "\n\n".join(all_text)
        
        if not full_text.strip():
            raise ValueError("PDF文件中没有提取到文本内容")
        
        logger.info(f"成功提取 {len(full_text)} 个字符")
        return full_text
        
    except Exception as e:
        logger.error(f"读取PDF文件失败: {e}")
        raise


def chunk_text(text: str, n: int, overlap: int, logger: Optional[logging.Logger] = None) -> List[str]:
    """
    将给定的文本分割为指定长度的片段，带有重叠字符
    
    Args:
        text: 需要分割的文本
        n: 每个片段的字符数量
        overlap: 段与段之间的重叠字符数量
        logger: 日志记录器
        
    Returns:
        List[str]: 包含文本片段的列表
        
    Raises:
        ValueError: 参数无效
    """
    logger = logger or setup_logging()
    
    if n <= 0:
        raise ValueError("n必须大于0")
    if overlap < 0:
        raise ValueError("overlap不能为负数")
    if overlap >= n:
        raise ValueError("overlap必须小于n")
    
    if not text:
        logger.warning("输入文本为空")
        return []
    
    chunks = []
    step = n - overlap
    
    for i in range(0, len(text), step):
        chunk = text[i:i + n]
        if chunk.strip():  # 只添加非空片段
            chunks.append(chunk)
    
    logger.info(f"文本分割完成，共生成 {len(chunks)} 个片段")
    return chunks


# ============================================================================
# Embedding处理模块
# ============================================================================

class EmbeddingManager:
    """
    Embedding管理器，支持缓存功能
    """
    
    def __init__(self, client: OpenAI, model: str, cache_file: str, logger: Optional[logging.Logger] = None):
        """
        初始化Embedding管理器
        
        Args:
            client: OpenAI客户端
            model: embedding模型名称
            cache_file: 缓存文件路径
            logger: 日志记录器
        """
        self.client = client
        self.model = model
        self.cache_file = cache_file
        self.logger = logger or setup_logging()
        self.cache: Dict[str, List[float]] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """从文件加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                self.cache = load_json(self.cache_file) or {}
                self.logger.info(f"已加载 {len(self.cache)} 个缓存的embeddings")
            except Exception as e:
                self.logger.warning(f"加载embedding缓存失败: {e}，将创建新缓存")
                self.cache = {}
        else:
            self.logger.info("未找到缓存文件，将创建新缓存")
    
    def _save_cache(self) -> None:
        """保存缓存到文件"""
        try:
            save_json(self.cache, self.cache_file)
            self.logger.debug(f"缓存已保存到 {self.cache_file}")
        except Exception as e:
            self.logger.warning(f"保存embedding缓存失败: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的embedding，支持缓存
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: embedding向量
        """
        text_hash = compute_text_hash(text)
        
        # 检查缓存
        if text_hash in self.cache:
            self.logger.debug(f"命中缓存: {text_hash[:8]}...")
            return self.cache[text_hash]
        
        # 调用API获取embedding
        try:
            self.logger.debug(f"调用API获取embedding: {text_hash[:8]}...")
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding
            
            # 保存到缓存
            self.cache[text_hash] = embedding
            self._save_cache()
            
            return embedding
            
        except AuthenticationError:
            raise ValueError("API认证失败，请检查API密钥是否正确")
        except RateLimitError:
            raise ValueError("API请求频率超限，请稍后重试")
        except APIError as e:
            raise ValueError(f"API请求失败: {e}")
    
    def get_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        批量获取文本的embeddings
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            List[List[float]]: embedding向量列表
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            self.logger.debug(f"处理批次 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            for text in batch:
                try:
                    embedding = self.get_embedding(text)
                    embeddings.append(embedding)
                except Exception as e:
                    self.logger.error(f"获取embedding失败: {e}")
                    raise
        
        return embeddings


# ============================================================================
# 相似度计算模块
# ============================================================================

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    计算两个向量之间的余弦相似度
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 余弦相似度值（-1到1之间）
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


# ============================================================================
# 语义搜索模块
# ============================================================================

@dataclass
class SearchResult:
    """搜索结果数据结构"""
    chunk: str
    score: float
    index: int


class SemanticSearcher:
    """
    语义搜索引擎
    """
    
    def __init__(self, text_chunks: List[str], embedding_manager: EmbeddingManager, 
                 logger: Optional[logging.Logger] = None):
        """
        初始化语义搜索引擎
        
        Args:
            text_chunks: 文本片段列表
            embedding_manager: embedding管理器
            logger: 日志记录器
        """
        self.text_chunks = text_chunks
        self.embedding_manager = embedding_manager
        self.logger = logger or setup_logging()
    
    def search(self, query: str, k: int = 5, min_score: float = 0.0) -> List[SearchResult]:
        """
        执行语义搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            min_score: 最小相似度分数阈值
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        if not query:
            raise ValueError("查询文本不能为空")
        
        if not self.text_chunks:
            raise ValueError("没有可搜索的文本片段")
        
        k = min(k, len(self.text_chunks))
        
        self.logger.info(f"正在搜索，查询: '{query[:50]}...'，k={k}")
        
        # 获取查询的embedding
        query_embedding = self.embedding_manager.get_embedding(query)
        query_vec = np.array(query_embedding)
        
        # 计算与所有片段的相似度
        similarity_scores = []
        for i, chunk in enumerate(self.text_chunks):
            chunk_embedding = self.embedding_manager.get_embedding(chunk)
            chunk_vec = np.array(chunk_embedding)
            
            score = cosine_similarity(query_vec, chunk_vec)
            similarity_scores.append((i, score))
        
        # 按相似度降序排序
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 构建结果
        results = []
        for idx, score in similarity_scores[:k]:
            if score >= min_score:
                results.append(SearchResult(
                    chunk=self.text_chunks[idx],
                    score=score,
                    index=idx
                ))
        
        self.logger.info(f"搜索完成，返回 {len(results)} 个结果")
        return results


# ============================================================================
# RAG系统核心
# ============================================================================

class SimpleRAG:
    """
    Simple RAG系统核心类
    整合PDF处理、embedding、语义搜索和生成功能
    """
    
    def __init__(self, config: Optional[RAGConfig] = None, logger: Optional[logging.Logger] = None):
        """
        初始化Simple RAG系统
        
        Args:
            config: RAG配置对象
            logger: 日志记录器
        """
        # 加载环境变量
        load_dotenv()
        
        # 设置配置
        self.config = config or RAGConfig()
        self.config.validate()
        
        # 设置日志
        self.logger = logger or setup_logging(self.config.log_level)
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key
        )
        
        # 系统提示
        self.system_prompt = (
            "你是一个严谨的AI助手，必须严格基于提供的上下文信息来回答问题。\n"
            "如果上下文中没有足够的信息来回答问题，你应该明确回复：'根据提供的信息，我无法回答这个问题。'\n"
            "不要编造或推测答案，只能基于上下文进行回答。"
        )
        
        # 内部状态
        self.text_chunks: List[str] = []
        self.embedding_manager: Optional[EmbeddingManager] = None
        self.searcher: Optional[SemanticSearcher] = None
        self._initialized = False
    
    def load_document(self, pdf_path: str) -> int:
        """
        加载并处理PDF文档
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            int: 文本片段数量
        """
        self.logger.info(f"正在加载文档: {pdf_path}")
        
        # 提取文本
        text = extract_text_from_pdf(pdf_path, self.logger)
        
        # 文本分块
        self.text_chunks = chunk_text(
            text, 
            self.config.chunk_size, 
            self.config.chunk_overlap,
            self.logger
        )
        
        if not self.text_chunks:
            raise ValueError("文档处理后没有生成有效的文本片段")
        
        # 初始化embedding管理器
        self.embedding_manager = EmbeddingManager(
            client=self.client,
            model=self.config.embedding_model,
            cache_file=self.config.embedding_cache_file,
            logger=self.logger
        )
        
        # 初始化搜索引擎
        self.searcher = SemanticSearcher(
            text_chunks=self.text_chunks,
            embedding_manager=self.embedding_manager,
            logger=self.logger
        )
        
        self._initialized = True
        self.logger.info("文档加载完成")
        
        return len(self.text_chunks)
    
    def query(self, question: str, top_k: Optional[int] = None, 
              show_context: bool = False) -> Dict[str, Any]:
        """
        查询RAG系统
        
        Args:
            question: 用户问题
            top_k: 返回的上下文片段数量
            show_context: 是否在返回结果中包含上下文片段
            
        Returns:
            Dict[str, Any]: 包含答案和元数据的字典
        """
        if not self._initialized:
            raise RuntimeError("请先调用load_document()加载文档")
        
        if not question:
            raise ValueError("问题不能为空")
        
        top_k = top_k or self.config.top_k
        
        self.logger.info(f"处理查询: '{question}'")
        
        # 语义搜索
        search_results = self.searcher.search(question, k=top_k)
        
        if not search_results:
            return {
                "question": question,
                "answer": "没有找到相关的上下文信息。",
                "sources": []
            }
        
        # 构建上下文
        context_parts = []
        for i, result in enumerate(search_results):
            context_parts.append(f"【来源 {i+1}】(相似度: {result.score:.4f})\n{result.chunk}\n")
        
        context = "\n".join(context_parts)
        
        # 构建prompt
        user_prompt = f"请根据以下上下文信息回答问题。\n\n{context}\n\n问题: {question}"
        
        # 生成回答
        try:
            response = self.client.chat.completions.create(
                model=self.config.chat_model,
                temperature=0,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            answer = response.choices[0].message.content
            
            result = {
                "question": question,
                "answer": answer,
                "num_sources": len(search_results)
            }
            
            if show_context:
                result["sources"] = [
                    {
                        "index": r.index,
                        "score": r.score,
                        "text": r.chunk
                    }
                    for r in search_results
                ]
            
            return result
            
        except AuthenticationError:
            raise ValueError("API认证失败，请检查API密钥是否正确")
        except RateLimitError:
            raise ValueError("API请求频率超限，请稍后重试")
        except APIError as e:
            raise ValueError(f"生成回答失败: {e}")
    
    def interactive_mode(self):
        """
        启动交互式查询模式
        """
        print("\n" + "="*60)
        print("Simple RAG 交互式查询模式")
        print("="*60)
        print("提示: 输入 'quit' 或 'exit' 退出程序")
        print("="*60 + "\n")
        
        while True:
            try:
                question = input("请输入您的问题: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q', '退出']:
                    print("感谢使用，再见！")
                    break
                
                if not question:
                    print("问题不能为空，请重新输入。\n")
                    continue
                
                result = self.query(question, show_context=True)
                
                print("\n" + "-"*60)
                print("回答:")
                print(result["answer"])
                print("-"*60)
                print(f"(参考来源: {result['num_sources']} 个片段)\n")
                
            except KeyboardInterrupt:
                print("\n\n程序被用户中断，感谢使用，再见！")
                break
            except Exception as e:
                print(f"\n处理查询时出错: {e}\n")


# ============================================================================
# 命令行界面
# ============================================================================

def parse_args():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="Simple RAG - 开箱即用的文档问答系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 加载PDF并回答问题
  python simple_rag.py --pdf data/document.pdf --query "文档的主要内容是什么？"
  
  # 交互式查询模式
  python simple_rag.py --pdf data/document.pdf --interactive
  
  # 自定义参数
  python simple_rag.py --pdf data/document.pdf --chunk-size 500 --top-k 3
        """
    )
    
    # 必需参数
    parser.add_argument(
        "--pdf", "-p",
        type=str,
        help="PDF文件路径"
    )
    
    # 查询相关
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="要查询的问题（单次查询模式）"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="启动交互式查询模式"
    )
    
    # PDF处理参数
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="文本分块大小（字符数），默认: 1000"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="分块重叠大小（字符数），默认: 200"
    )
    
    # 搜索参数
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="返回的最相关片段数量，默认: 5"
    )
    
    # API参数
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API密钥（也可通过环境变量OPENAI_API_KEY设置）"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        help="API基础URL（也可通过环境变量OPENAI_BASE_URL设置）"
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="text-embedding-ada-002",
        help="Embedding模型名称，默认: text-embedding-ada-002"
    )
    parser.add_argument(
        "--chat-model",
        type=str,
        default="gpt-4o",
        help="聊天模型名称，默认: gpt-4o"
    )
    
    # 其他参数
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="在输出中显示参考的上下文片段"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=".cache",
        help="Embedding缓存目录，默认: .cache"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别，默认: INFO"
    )
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    # 解析参数
    args = parse_args()
    
    # 验证参数
    if not args.pdf:
        print("错误: 请指定PDF文件路径 (--pdf)")
        sys.exit(1)
    
    if not args.query and not args.interactive:
        print("错误: 请指定查询问题 (--query) 或启动交互式模式 (--interactive)")
        sys.exit(1)
    
    # 创建配置
    config = RAGConfig(
        api_key=args.api_key or os.getenv("OPENAI_API_KEY", ""),
        base_url=args.base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        embedding_model=args.embedding_model,
        chat_model=args.chat_model,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        top_k=args.top_k,
        cache_dir=args.cache_dir,
        embedding_cache_file=os.path.join(args.cache_dir, "embeddings.json"),
        log_level=args.log_level
    )
    
    # 初始化RAG系统
    logger = setup_logging(args.log_level)
    
    try:
        rag = SimpleRAG(config=config, logger=logger)
        
        # 加载文档
        rag.load_document(args.pdf)
        
        # 执行查询
        if args.interactive:
            rag.interactive_mode()
        else:
            result = rag.query(args.query, show_context=args.show_context)
            
            print("\n" + "="*60)
            print("问题:", result["question"])
            print("="*60)
            print("\n回答:")
            print(result["answer"])
            print("\n" + "-"*60)
            print(f"参考来源: {result['num_sources']} 个片段")
            
            if args.show_context and "sources" in result:
                print("\n" + "="*60)
                print("上下文片段详情:")
                print("="*60)
                for i, source in enumerate(result["sources"]):
                    print(f"\n【来源 {i+1}】(索引: {source['index']}, 相似度: {source['score']:.4f})")
                    print("-"*40)
                    print(source["text"][:500] + "..." if len(source["text"]) > 500 else source["text"])
    
    except ValueError as e:
        logger.error(f"配置或参数错误: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
