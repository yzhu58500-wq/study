"""
基础使用示例
"""
import asyncio
from doc_extractor import extract_from_file


async def main():
    """基础使用示例"""
    
    # 示例1: 从文件提取
    print("=" * 60)
    print("示例1: 从文件提取")
    print("=" * 60)
    
    results = await extract_from_file(
        file_path="test.md",
        keywords=["土壤", "环境", "位置"],
        top_k=10
    )
    
    for keyword, matches in results.items():
        print(f"\n【{keyword}】找到 {len(matches)} 个结果")
        for i, match in enumerate(matches[:3], 1):  # 只显示前3个
            print(f"\n{i}. {match[:150]}{'...' if len(match) > 150 else ''}")
    
    # 示例2: 从文本提取
    print("\n" + "=" * 60)
    print("示例2: 从文本提取")
    print("=" * 60)
    
    markdown_text = """
# 第一章 项目概况

## 1.1 项目位置

本项目位于XX省XX市XX县XX镇，地理坐标为东经118°32'45"，北纬32°15'30"。

## 1.2 土壤条件

土壤类型为红壤和黄壤，pH值5.5-6.5，有机质含量1.2-2.5%。

# 第二章 环境现状

## 2.1 气候特征

项目区域属亚热带季风气候区，年平均气温16.5℃，年降水量1250mm。
"""
    
    from doc_extractor import extract_from_markdown
    
    results = await extract_from_markdown(
        markdown_text=markdown_text,
        keywords=["土壤", "气候"]
    )
    
    for keyword, matches in results.items():
        print(f"\n【{keyword}】")
        for match in matches:
            print(f"- {match}")
    
    print("\n✓ 示例执行完成")


if __name__ == "__main__":
    asyncio.run(main())
