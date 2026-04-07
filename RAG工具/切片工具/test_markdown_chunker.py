"""
测试脚本 - Markdown文件切分功能测试

使用方法：
python test_markdown_chunker.py <Markdown文件路径> [最大字符数] [最小字符数]

示例：
python test_markdown_chunker.py ./test.md
python test_markdown_chunker.py ./test.md 1000 100
"""
import sys
from pathlib import Path
from rag_modules import MarkdownChunker


def main():
    # 检查参数
    if len(sys.argv) < 2:
        print("使用方法: python test_markdown_chunker.py <Markdown文件路径> [最大字符数] [最小字符数]")
        print("示例:")
        print("  python test_markdown_chunker.py ./test.md")
        print("  python test_markdown_chunker.py ./test.md 1000")
        print("  python test_markdown_chunker.py ./test.md 1000 100")
        sys.exit(1)
    
    md_path = sys.argv[1]
    max_chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else None
    min_chunk_size = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # 检查文件是否存在
    if not Path(md_path).exists():
        print(f"错误: 文件不存在: {md_path}")
        sys.exit(1)
    
    print(f"开始处理Markdown文件: {md_path}")
    if max_chunk_size:
        print(f"最大chunk大小: {max_chunk_size} 字符")
    if min_chunk_size:
        print(f"最小chunk大小: {min_chunk_size} 字符")
    print("="*60)
    
    # 创建解析器
    chunker = MarkdownChunker(
        table_merge_threshold=23.0,
        max_chunk_size=max_chunk_size,
        min_chunk_size=min_chunk_size
    )
    
    try:
        # 加载并切分chunks
        chunks = chunker.process_file(md_path, merge_tables=True)
        
        print(f"切分完成！共生成 {len(chunks)} 个chunks")
        print("="*60)
        
        # 显示chunk摘要
        print("\nChunk摘要:")
        for chunk in chunks[:5]:  # 显示前5个
            print(f"\n[{chunk.chunk_id}] {chunk.level_2_title}")
            print(f"    一级标题: {chunk.level_1_title}")
            print(f"    编号: L1-{chunk.level_1_index}, L2-{chunk.level_2_index}")
            print(f"    包含表格: {chunk.has_table}")
            print(f"    字符数: {len(chunk.content)}")
            
            # 显示大小警告
            if max_chunk_size and len(chunk.content) > max_chunk_size:
                print(f"    ⚠️  超过最大限制!")
            if min_chunk_size and len(chunk.content) < min_chunk_size:
                print(f"    ⚠️  低于最小限制!")
        
        if len(chunks) > 5:
            print(f"\n... 还有 {len(chunks) - 5} 个chunks")
        
        # 统计信息
        if max_chunk_size or min_chunk_size:
            print("\n大小统计:")
            sizes = [len(c.content) for c in chunks]
            print(f"  平均大小: {sum(sizes)//len(sizes)} 字符")
            print(f"  最小: {min(sizes)} 字符")
            print(f"  最大: {max(sizes)} 字符")
            
            if max_chunk_size:
                oversized = sum(1 for s in sizes if s > max_chunk_size)
                print(f"  超大chunks: {oversized}")
            
            if min_chunk_size:
                undersized = sum(1 for s in sizes if s < min_chunk_size)
                print(f"  过小chunks: {undersized}")
        
        # 保存结果
        output_txt = Path(md_path).stem + "_chunks.txt"
        output_json = Path(md_path).stem + "_chunks.json"
        
        chunker.save_chunks(chunks, output_txt, format='txt')
        chunker.save_chunks(chunks, output_json, format='json')
        
        print(f"\n结果已保存:")
        print(f"  - 文本格式: {output_txt}")
        print(f"  - JSON格式: {output_json}")
        print("="*60)
        
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
