"""
Markdown Chunker模块 - 对Markdown文件进行切分

主要功能：
1. 按二级标题切分chunk
2. 表格处理（跨页/跨栏合并）
3. 提取元数据
4. Chunk大小控制（最大/最小值）
"""
import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Chunk:
    """Chunk数据结构"""
    chunk_id: int
    content: str
    level_1_title: str  # 所属一级标题
    level_2_title: str  # 二级标题（本chunk标题）
    level_1_index: Optional[int] = None  # 一级标题编号
    level_2_index: Optional[int] = None  # 二级标题编号
    page_numbers: List[int] = None  # 所在页码
    has_table: bool = False  # 是否包含表格
    metadata: Dict = None  # 其他元数据
    
    def __post_init__(self):
        if self.page_numbers is None:
            self.page_numbers = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class TableMerger:
    """表格合并处理器"""
    
    def __init__(self, threshold: float = 23.0):
        self.threshold = threshold  # 字符宽度倍数阈值
    
    def detect_and_merge_tables(self, markdown_content: str) -> str:
        """
        检测并合并表格
        
        逻辑：
        1. 同一页且表头表题相同 → 跨栏表格，合并
        2. 跨一页且无中间字符 + 距离 < 阈值 → 跨页表格，合并
        3. 跨两页 → 不同表格
        """
        lines = markdown_content.split('\n')
        tables = self._extract_tables(lines)
        
        if not tables:
            return markdown_content
        
        # 分析表格关系
        merged_tables = self._analyze_and_merge(tables, lines)
        
        # 重建markdown
        return self._rebuild_markdown(lines, merged_tables)
    
    def _extract_tables(self, lines: List[str]) -> List[Dict]:
        """提取所有表格信息"""
        tables = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if '|' in line and i + 1 < len(lines) and '---' in lines[i+1]:
                # 找到表格开始
                table_info = {
                    'start_line': i,
                    'end_line': i,
                    'header': line,
                    'page': self._get_page_number(lines, i),
                    'position': self._get_position(lines, i),
                    'content': []
                }
                
                # 读取整个表格
                j = i
                while j < len(lines) and (lines[j].strip() == '' or '|' in lines[j] or '---' in lines[j]):
                    table_info['content'].append(lines[j])
                    j += 1
                
                table_info['end_line'] = j - 1
                table_info['content_str'] = '\n'.join(table_info['content'])
                tables.append(table_info)
                i = j
            else:
                i += 1
        
        return tables
    
    def _get_page_number(self, lines: List[str], line_idx: int) -> int:
        """获取行所在页码（从Markdown注释或标记中提取）"""
        for i in range(line_idx, -1, -1):
            if lines[i].startswith('<!-- Page'):
                match = re.search(r'Page\s+(\d+)', lines[i])
                if match:
                    return int(match.group(1))
        return -1
    
    def _get_position(self, lines: List[str], line_idx: int) -> Tuple[float, float]:
        """获取表格在页面中的位置（用于计算距离）"""
        return (0.0, 1.0)
    
    def _analyze_and_merge(self, tables: List[Dict], lines: List[str]) -> List[Dict]:
        """分析表格关系并合并"""
        if len(tables) <= 1:
            return tables
        
        merged = []
        i = 0
        
        while i < len(tables):
            current_table = tables[i]
            
            # 检查是否需要与下一个表格合并
            if i + 1 < len(tables):
                next_table = tables[i + 1]
                merge_type = self._should_merge(current_table, next_table, lines)
                
                if merge_type == 'cross_column':
                    # 跨栏表格：同一页且表头相同
                    merged_table = self._merge_tables(current_table, next_table)
                    merged.append(merged_table)
                    i += 2
                    continue
                elif merge_type == 'cross_page':
                    # 跨页表格：跨一页且距离符合要求
                    merged_table = self._merge_tables(current_table, next_table)
                    merged.append(merged_table)
                    i += 2
                    continue
            
            merged.append(current_table)
            i += 1
        
        return merged
    
    def _should_merge(self, table1: Dict, table2: Dict, lines: List[str]) -> Optional[str]:
        """
        判断两个表格是否需要合并
        
        返回：
        - 'cross_column': 跨栏表格
        - 'cross_page': 跨页表格
        - None: 不合并
        """
        page1, page2 = table1['page'], table2['page']
        header1, header2 = table1['header'], table2['header']
        
        # 情况1：跨两页 → 不合并
        if abs(page2 - page1) >= 2:
            return None
        
        # 情况2：同一页且表头相同 → 跨栏表格
        if page1 == page2 and header1.strip() == header2.strip():
            return 'cross_column'
        
        # 情况3：跨一页
        if abs(page2 - page1) == 1:
            # 检查中间是否有文本内容
            has_text = self._check_text_between(table1, table2, lines)
            
            if not has_text:
                # 计算距离
                distance = self._calculate_distance(table1, table2)
                
                if distance < self.threshold:
                    return 'cross_page'
        
        return None
    
    def _check_text_between(self, table1: Dict, table2: Dict, lines: List[str]) -> bool:
        """检查两个表格之间是否有文本内容"""
        start = table1['end_line'] + 1
        end = table2['start_line']
        
        for i in range(start, end):
            if lines[i].strip() and not lines[i].startswith('<!--'):
                return True
        
        return False
    
    def _calculate_distance(self, table1: Dict, table2: Dict) -> float:
        """
        计算表格间距离
        
        距离 = table1下边缘到下页边 + table2上边缘到上页边
        """
        pos1 = table1.get('position', (0, 1))
        pos2 = table2.get('position', (0, 1))
        
        distance = (1.0 - pos1[1]) + pos2[0]
        char_width = 0.01
        
        return distance / char_width
    
    def _merge_tables(self, table1: Dict, table2: Dict) -> Dict:
        """合并两个表格"""
        merged = table1.copy()
        merged['end_line'] = table2['end_line']
        merged['content'] = table1['content'] + table2['content'][2:]  # 跳过第二个表头
        merged['content_str'] = '\n'.join(merged['content'])
        return merged
    
    def _rebuild_markdown(self, lines: List[str], merged_tables: List[Dict]) -> str:
        """重建markdown内容"""
        result = []
        
        i = 0
        while i < len(lines):
            in_table = False
            for table in merged_tables:
                if i == table['start_line']:
                    result.append(table['content_str'])
                    i = table['end_line'] + 1
                    in_table = True
                    break
            
            if not in_table:
                result.append(lines[i])
                i += 1
        
        return '\n'.join(result)


class MarkdownChunker:
    """Markdown文件切分主类"""
    
    def __init__(self, 
                 table_merge_threshold: float = 23.0,
                 max_chunk_size: Optional[int] = None,
                 min_chunk_size: Optional[int] = None):
        """
        初始化Markdown切分器
        
        Args:
            table_merge_threshold: 表格合并阈值
            max_chunk_size: chunk最大字符数（None表示不限制）
            min_chunk_size: chunk最小字符数（None表示不限制）
        """
        self.table_merger = TableMerger(table_merge_threshold)
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
    
    def load_markdown(self, md_path: str) -> str:
        """
        加载Markdown文件
        
        Args:
            md_path: Markdown文件路径
        
        Returns:
            markdown内容
        """
        md_path = Path(md_path)
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown文件不存在: {md_path}")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    def chunk_by_headings(self, markdown_content: str, merge_tables: bool = True) -> List[Chunk]:
        """
        按二级标题切分chunk
        
        规则：
        - 从二级标题开始，到下一个二级标题前结束
        - 每个chunk包含一个二级标题及其内容
        - 记录所属的一级标题名称
        
        Args:
            markdown_content: Markdown内容
            merge_tables: 是否合并表格
        """
        # 处理表格合并
        if merge_tables:
            markdown_content = self.table_merger.detect_and_merge_tables(markdown_content)
        
        chunks = []
        lines = markdown_content.split('\n')
        
        current_chunk = None
        current_level1_title = ""
        level_1_index = 0
        level_2_index = 0
        
        for line in lines:
            # 检测一级标题
            if line.startswith('# ') and not line.startswith('## '):
                current_level1_title = line[2:].strip()
                level_1_index += 1
                level_2_index = 0
                continue
            
            # 检测二级标题
            if line.startswith('## '):
                # 保存上一个chunk
                if current_chunk is not None:
                    chunks.append(current_chunk)
                
                # 开始新chunk
                level_2_index += 1
                level_2_title = line[3:].strip()
                current_chunk = Chunk(
                    chunk_id=len(chunks),
                    content=line + '\n',
                    level_1_title=current_level1_title,
                    level_2_title=level_2_title,
                    level_1_index=level_1_index,
                    level_2_index=level_2_index,
                    has_table=False
                )
            else:
                # 添加内容到当前chunk
                if current_chunk is not None:
                    current_chunk.content += line + '\n'
                    # 检测是否包含表格
                    if '|' in line and '---' not in line:
                        current_chunk.has_table = True
        
        # 添加最后一个chunk
        if current_chunk is not None:
            chunks.append(current_chunk)
        
        # 清理内容
        for chunk in chunks:
            chunk.content = chunk.content.strip()
            chunk.page_numbers = self._extract_page_numbers(chunk.content)
        
        # 应用大小控制
        if self.max_chunk_size or self.min_chunk_size:
            chunks = self._apply_size_constraints(chunks)
        
        return chunks
    
    def _apply_size_constraints(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        应用chunk大小限制
        
        Args:
            chunks: 原始chunks
        
        Returns:
            处理后的chunks
        """
        processed_chunks = []
        
        for chunk in chunks:
            chunk_size = len(chunk.content)
            
            # 处理超大chunk（拆分）
            if self.max_chunk_size and chunk_size > self.max_chunk_size:
                split_chunks = self._split_large_chunk(chunk)
                processed_chunks.extend(split_chunks)
            
            # 处理过小chunk（标记，后续可能合并）
            elif self.min_chunk_size and chunk_size < self.min_chunk_size:
                # 尝试与上一个chunk合并
                if processed_chunks and processed_chunks[-1].level_1_title == chunk.level_1_title:
                    merged_chunk = self._merge_chunks(processed_chunks[-1], chunk)
                    processed_chunks[-1] = merged_chunk
                else:
                    # 无法合并，保留但添加标记
                    chunk.metadata['small_chunk'] = True
                    processed_chunks.append(chunk)
            else:
                processed_chunks.append(chunk)
        
        # 重新编号
        for i, chunk in enumerate(processed_chunks):
            chunk.chunk_id = i
        
        return processed_chunks
    
    def _split_large_chunk(self, chunk: Chunk) -> List[Chunk]:
        """
        拆分超大chunk
        
        Args:
            chunk: 需要拆分的chunk
        
        Returns:
            拆分后的chunks列表
        """
        paragraphs = chunk.content.split('\n\n')
        split_chunks = []
        
        current_content = ""
        current_size = 0
        part_num = 1
        
        for para in paragraphs:
            para_size = len(para) + 2  # 加上\n\n
            
            # 如果单个段落就超过最大值，按句子拆分
            if para_size > self.max_chunk_size:
                # 先保存当前内容
                if current_content:
                    new_chunk = self._create_chunk_from_content(
                        current_content.strip(),
                        chunk,
                        part_num
                    )
                    split_chunks.append(new_chunk)
                    part_num += 1
                    current_content = ""
                    current_size = 0
                
                # 按句子拆分大段落
                sentences = re.split(r'([。！？\n])', para)
                temp_content = ""
                
                for i in range(0, len(sentences) - 1, 2):
                    sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                    
                    if len(temp_content) + len(sentence) > self.max_chunk_size:
                        if temp_content:
                            new_chunk = self._create_chunk_from_content(
                                temp_content.strip(),
                                chunk,
                                part_num
                            )
                            split_chunks.append(new_chunk)
                            part_num += 1
                            temp_content = sentence
                        else:
                            # 单个句子就超限，强制截断
                            new_chunk = self._create_chunk_from_content(
                                sentence[:self.max_chunk_size],
                                chunk,
                                part_num
                            )
                            split_chunks.append(new_chunk)
                            part_num += 1
                            temp_content = sentence[self.max_chunk_size:]
                    else:
                        temp_content += sentence
                
                if temp_content:
                    current_content = temp_content
                    current_size = len(temp_content)
            
            # 正常情况：添加段落
            elif current_size + para_size > self.max_chunk_size:
                # 当前内容已经够大，创建新chunk
                if current_content:
                    new_chunk = self._create_chunk_from_content(
                        current_content.strip(),
                        chunk,
                        part_num
                    )
                    split_chunks.append(new_chunk)
                    part_num += 1
                
                current_content = para
                current_size = para_size
            else:
                current_content += '\n\n' + para if current_content else para
                current_size += para_size
        
        # 添加最后一部分
        if current_content:
            new_chunk = self._create_chunk_from_content(
                current_content.strip(),
                chunk,
                part_num
            )
            split_chunks.append(new_chunk)
        
        return split_chunks if split_chunks else [chunk]
    
    def _create_chunk_from_content(self, content: str, original_chunk: Chunk, part_num: int) -> Chunk:
        """
        从内容创建新chunk
        
        Args:
            content: 内容
            original_chunk: 原始chunk
            part_num: 部分编号
        
        Returns:
            新chunk
        """
        # 提取标题（如果有）
        lines = content.split('\n')
        title = original_chunk.level_2_title
        if lines and lines[0].startswith('## '):
            title = lines[0][3:].strip()
        
        return Chunk(
            chunk_id=0,  # 稍后重新编号
            content=content,
            level_1_title=original_chunk.level_1_title,
            level_2_title=f"{title} (Part {part_num})",
            level_1_index=original_chunk.level_1_index,
            level_2_index=original_chunk.level_2_index,
            has_table='|' in content,
            metadata={'split_from': original_chunk.chunk_id, 'part': part_num}
        )
    
    def _merge_chunks(self, chunk1: Chunk, chunk2: Chunk) -> Chunk:
        """
        合并两个chunk
        
        Args:
            chunk1: 第一个chunk
            chunk2: 第二个chunk
        
        Returns:
            合并后的chunk
        """
        merged_content = chunk1.content + '\n\n' + chunk2.content
        
        # 合并页码
        merged_pages = list(set(chunk1.page_numbers + chunk2.page_numbers))
        
        return Chunk(
            chunk_id=chunk1.chunk_id,
            content=merged_content,
            level_1_title=chunk1.level_1_title,
            level_2_title=chunk1.level_2_title,
            level_1_index=chunk1.level_1_index,
            level_2_index=chunk1.level_2_index,
            has_table=chunk1.has_table or chunk2.has_table,
            metadata={'merged_from': [chunk1.chunk_id, chunk2.chunk_id]}
        )
    
    def _extract_page_numbers(self, content: str) -> List[int]:
        """从内容中提取页码"""
        pages = []
        matches = re.findall(r'<!--\s*Page\s+(\d+)', content)
        for m in matches:
            pages.append(int(m))
        return list(set(pages))
    
    def process_file(self, md_path: str, merge_tables: bool = True) -> List[Chunk]:
        """
        完整处理流程：加载Markdown → 切分chunk
        
        这是一行代码调用的接口
        
        Args:
            md_path: Markdown文件路径
            merge_tables: 是否合并表格
        """
        content = self.load_markdown(md_path)
        chunks = self.chunk_by_headings(content, merge_tables)
        return chunks
    
    def save_chunks(self, chunks: List[Chunk], output_path: str, format: str = 'txt'):
        """
        保存chunks到文件
        
        Args:
            chunks: chunk列表
            output_path: 输出路径
            format: 输出格式 (txt / json)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            data = [chunk.to_dict() for chunk in chunks]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                for chunk in chunks:
                    f.write(f"{'='*60}\n")
                    f.write(f"Chunk ID: {chunk.chunk_id}\n")
                    f.write(f"一级标题: {chunk.level_1_title}\n")
                    f.write(f"二级标题: {chunk.level_2_title}\n")
                    f.write(f"标题编号: L1-{chunk.level_1_index}, L2-{chunk.level_2_index}\n")
                    f.write(f"页码: {chunk.page_numbers}\n")
                    f.write(f"包含表格: {chunk.has_table}\n")
                    f.write(f"字符数: {len(chunk.content)}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(chunk.content)
                    f.write("\n\n")


# 便捷函数：一行代码调用
def chunk_markdown(md_path: str, 
                   merge_tables: bool = True,
                   max_chunk_size: Optional[int] = None,
                   min_chunk_size: Optional[int] = None) -> List[Chunk]:
    """
    一行代码切分Markdown文件
    
    用法：
        chunks = chunk_markdown("document.md")
        chunks = chunk_markdown("document.md", max_chunk_size=1000)
        chunks = chunk_markdown("document.md", max_chunk_size=1000, min_chunk_size=100)
    
    Args:
        md_path: Markdown文件路径
        merge_tables: 是否合并表格
        max_chunk_size: chunk最大字符数
        min_chunk_size: chunk最小字符数
    """
    chunker = MarkdownChunker(
        max_chunk_size=max_chunk_size,
        min_chunk_size=min_chunk_size
    )
    return chunker.process_file(md_path, merge_tables)
