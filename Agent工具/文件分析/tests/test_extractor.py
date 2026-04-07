"""
单元测试
"""
import pytest
import asyncio
from doc_extractor import DocExtractor, extract_from_markdown


@pytest.fixture
def sample_markdown():
    """测试用的Markdown文本"""
    return """
# 第一章 项目概况

## 1.1 项目位置

本项目位于XX省XX市XX县XX镇，地理坐标为东经118°32'45"，北纬32°15'30"。

## 1.2 土壤条件

土壤类型为红壤和黄壤，pH值5.5-6.5，有机质含量1.2-2.5%。

# 第二章 环境现状

## 2.1 气候特征

项目区域属亚热带季风气候区，年平均气温16.5℃，年降水量1250mm。

## 2.2 土壤环境

土壤质地以壤土和粘壤土为主。
"""


@pytest.fixture
def extractor():
    """创建提取器实例"""
    return DocExtractor(top_k=10)


@pytest.mark.asyncio
async def test_extract_from_markdown(sample_markdown):
    """测试从Markdown提取"""
    results = await extract_from_markdown(
        markdown_text=sample_markdown,
        keywords=["土壤", "气候"],
        top_k=10
    )
    
    # 验证返回格式
    assert isinstance(results, dict)
    assert "土壤" in results
    assert "气候" in results
    
    # 验证有结果
    assert len(results["土壤"]) > 0
    assert len(results["气候"]) > 0


@pytest.mark.asyncio
async def test_extractor_class(sample_markdown, extractor):
    """测试提取器类"""
    results = await extractor.extract(sample_markdown, ["土壤"])
    
    assert "土壤" in results
    assert len(results["土壤"]) > 0


@pytest.mark.asyncio
async def test_parse_sections(extractor):
    """测试章节解析"""
    sections = extractor._parse_sections(sample_markdown)
    
    # 验证章节数量
    assert len(sections) == 4
    
    # 验证章节结构
    assert sections[0]['title'] == "第一章 项目概况"
    assert sections[0]['level'] == 1


@pytest.mark.asyncio
async def test_generate_key(extractor):
    """测试键生成"""
    text = "测试文本"
    key1 = extractor._generate_key(text)
    key2 = extractor._generate_key(text)
    
    # 相同文本生成相同键
    assert key1 == key2
    assert len(key1) == 16


@pytest.mark.asyncio
async def test_top_k_limit(sample_markdown):
    """测试Top-K限制"""
    # 只返回前3个结果
    extractor = DocExtractor(top_k=3)
    results = await extractor.extract(sample_markdown, ["土壤"])
    
    # 不超过3个
    assert len(results["土壤"]) <= 3


@pytest.mark.asyncio
async def test_empty_keywords(sample_markdown):
    """测试空关键词"""
    extractor = DocExtractor()
    results = await extractor.extract(sample_markdown, [])
    
    # 空关键词返回空字典
    assert len(results) == 0


@pytest.mark.asyncio
async def test_nonexistent_keyword(sample_markdown):
    """测试不存在的关键词"""
    extractor = DocExtractor()
    results = await extractor.extract(sample_markdown, ["不存在的关键词"])
    
    # 不存在的关键词返回空列表
    assert len(results["不存在的关键词"]) == 0


if __name__ == "__main__":
    pytest.main(["-v", "tests/test_extractor.py"])
