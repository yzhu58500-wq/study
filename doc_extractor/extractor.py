"""
核心提取器模块
"""
import json
import redis
import asyncio
from typing import List, Dict, Optional
from openai import AsyncOpenAI


class DocExtractor:
    """文档提取器"""
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        llm_api_key: str = "",
        llm_base_url: str = "https://api.openai.com/v1",
        llm_model: str = "gpt-4o-mini",
        top_k: int = 10
    ):
        """
        初始化提取器
        
        Args:
            redis_host: Redis地址
            redis_port: Redis端口
            redis_db: Redis数据库编号
            redis_password: Redis密码
            llm_api_key: LLM API密钥
            llm_base_url: LLM API地址
            llm_model: 模型名称
            top_k: 返回前K个结果
        """
        self.top_k = top_k
        
        # Redis连接
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )
        
        # LLM客户端
        if llm_api_key:
            self.llm = AsyncOpenAI(
                api_key=llm_api_key,
                base_url=llm_base_url
            )
        else:
            self.llm = None
        
        self.model = llm_model
    
    async def extract(
        self,
        markdown_text: str,
        keywords: List[str]
    ) -> Dict[str, List[str]]:
        """
        从Markdown提取关键词相关信息
        
        Args:
            markdown_text: Markdown格式的文本
            keywords: 关键词列表
            
        Returns:
            {关键词1: [结果1, 结果2, ..., 结果10],
             关键词2: [结果1, 结果2, ..., 结果10]}
        """
        return await self._extract_all_parallel(markdown_text, keywords)
    
    async def _extract_all_parallel(
        self,
        markdown_text: str,
        keywords: List[str]
    ) -> Dict[str, List[str]]:
        """并行提取所有关键词"""
        
        # Step 1: 解析章节结构
        sections = self._parse_sections(markdown_text)
        
        # Step 2: 存入Redis
        file_key = f"doc:{self._generate_key(markdown_text)}"
        self._save_to_redis(file_key, sections)
        
        # Step 3: 并行提取每个关键词
        tasks = [
            self._extract_keyword(file_key, keyword)
            for keyword in keywords
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Step 4: 整理结果
        return {
            keywords[i]: results[i] 
            for i in range(len(keywords))
        }
    
    def _parse_sections(self, markdown: str) -> List[Dict]:
        """解析Markdown章节结构"""
        import re
        
        lines = markdown.split('\n')
        sections = []
        current = None
        section_id = 0
        
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if match:
                if current:
                    current['content'] = '\n'.join(lines[current['start']:i])
                    sections.append(current)
                
                section_id += 1
                level = len(match.group(1))
                title = match.group(2).strip()
                
                current = {
                    'id': str(section_id),
                    'level': level,
                    'title': title,
                    'start': i,
                    'content': ''
                }
        
        if current:
            current['content'] = '\n'.join(lines[current['start']:])
            sections.append(current)
        
        return sections
    
    def _save_to_redis(self, key: str, sections: List[Dict]):
        """存入Redis"""
        self.redis.hset(
            key,
            mapping={
                'sections': json.dumps(sections, ensure_ascii=False),
                'count': len(sections),
                'created_at': self._get_timestamp()
            }
        )
    
    def _load_from_redis(self, key: str) -> Optional[List[Dict]]:
        """从Redis加载"""
        sections_json = self.redis.hget(key, 'sections')
        if sections_json:
            return json.loads(sections_json)
        return None
    
    async def _extract_keyword(self, file_key: str, keyword: str) -> List[str]:
        """提取单个关键词的前10个结果"""
        
        sections = self._load_from_redis(file_key)
        if not sections:
            return []
        
        matches = []
        
        for section in sections:
            title = section.get('title', '')
            content = section.get('content', '')
            
            # 标题匹配（权重高）
            title_score = 0
            if keyword in title:
                title_score += 10
            
            # 内容匹配（逐行计数）
            content_score = 0
            lines = content.split('\n')
            matched_lines = []
            
            for line in lines:
                if keyword in line:
                    content_score += 1
                    matched_lines.append(line.strip())
            
            total_score = title_score + content_score
            
            if total_score > 0:
                matches.append({
                    'title': title,
                    'content': matched_lines[:3],
                    'score': total_score
                })
        
        # 按分数排序，取前10
        matches.sort(key=lambda x: x['score'], reverse=True)
        top_matches = matches[:self.top_k]
        
        # 提取文本结果
        results = []
        for match in top_matches:
            result_text = f"【{match['title']}】\n" + '\n'.join(match['content'])
            results.append(result_text)
        
        return results
    
    def _generate_key(self, text: str) -> str:
        """生成文件唯一标识"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:16]
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d_%H%M%S')


async def extract_from_markdown(
    markdown_text: str,
    keywords: List[str],
    llm_api_key: str = "",
    top_k: int = 10,
    **kwargs
) -> Dict[str, List[str]]:
    """
    便捷函数：一行调用提取
    
    Args:
        markdown_text: Markdown文本
        keywords: 关键词列表
        llm_api_key: LLM API密钥（可选）
        top_k: 返回前K个结果
        **kwargs: 其他参数传递给DocExtractor
        
    Returns:
        {关键词: [结果1, 结果2, ...]}
    
    Example:
        >>> results = await extract_from_markdown(
        ...     markdown_content,
        ...     keywords=["土壤", "环境"]
        ... )
    """
    extractor = DocExtractor(
        llm_api_key=llm_api_key,
        top_k=top_k,
        **kwargs
    )
    
    return await extractor.extract(markdown_text, keywords)


async def extract_from_file(
    file_path: str,
    keywords: List[str],
    llm_api_key: str = "",
    top_k: int = 10,
    **kwargs
) -> Dict[str, List[str]]:
    """
    从文件提取
    
    Args:
        file_path: Markdown文件路径
        keywords: 关键词列表
        llm_api_key: LLM API密钥（可选）
        top_k: 返回前K个结果
        **kwargs: 其他参数传递给DocExtractor
    
    Example:
        >>> results = await extract_from_file(
        ...     "report.md",
        ...     keywords=["土壤", "环境"]
        ... )
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    return await extract_from_markdown(
        markdown_text, keywords, llm_api_key, top_k, **kwargs
    )
