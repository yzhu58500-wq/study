"""
JSON Parser Utilities
安全解析JSON响应的工具函数，处理markdown代码块和格式问题

"""

import json
import re
import logging
from typing import Dict, Any, Optional, List


# 配置日志
logger = logging.getLogger(__name__)


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    安全解析JSON响应，处理markdown代码块和格式问题
    
    Args:
        response: 原始响应字符串，可能包含markdown代码块或格式问题
        
    Returns:
        解析后的字典，解析失败时返回空字典
        
    Examples:
        >>> parse_json_response('```json\\n{"name": "test"}\\n```')
        {'name': 'test'}
        >>> parse_json_response('{"code": "print(\\"hello\\")"}')
        {'code': 'print("hello")'}
    """
    
    def fix_escaped_newlines(s: str) -> str:
        """修复过度转义的换行符"""
        # 处理多层转义: \\\\n -> \n, \\n -> \n
        s = s.replace('\\\\\\n', '\n')
        s = s.replace('\\n', '\n')
        # 处理可能的 \\r\\n
        s = s.replace('\\\\\\r', '\r')
        s = s.replace('\\r', '\r')
        return s
    
    def try_parse(s: str) -> Optional[Dict]:
        """尝试解析JSON，包含修复逻辑"""
        # 清理常见问题
        s = s.strip()
        
        # 移除可能的BOM
        if s.startswith('\ufeff'):
            s = s[1:]
        
        try:
            result = json.loads(s)
            # 成功解析后，修复值中的转义字符
            return _fix_escaped_values(result)
        except json.JSONDecodeError:
            pass
        
        # 尝试修复常见JSON问题
        try:
            # 修复无效的JSON转义序列 \[ \] \# 等 (LLM经常产生这种错误)
            # 需要在字符串值中修复，但避免影响已转义的反斜杠
            # \\[ 是有效的(表示 \[ 字面量)，但 \[ 不是有效的JSON转义
            s = re.sub(r'(?<!\\)\\([^\\"\'nrtbfu/])', r'\\\1', s)
            
            result = json.loads(s)
            return _fix_escaped_values(result)
        except json.JSONDecodeError:
            pass
        
        return None
    
    # 1. 尝试直接解析
    result = try_parse(response)
    if result:
        logger.debug("Direct JSON parse succeeded")
        return result
    
    # 2. 处理markdown代码块 ```json ... ```
    json_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(json_block_pattern, response, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        result = try_parse(json_str)
        if result:
            logger.debug("Extracted JSON from markdown code block")
            return result
    
    # 3. 尝试提取 {} 之间的内容
    start = response.find('{')
    end = response.rfind('}')
    if start != -1 and end != -1 and end > start:
        result = try_parse(response[start:end+1])
        if result:
            logger.debug("Extracted JSON from braces")
            return result
    
    # 4. 最后尝试用更宽松的方式解析
    try:
        # 使用 ast.literal_eval 作为备选
        import ast
        # 将 true/false/null 转换为 Python 格式
        s = response
        s = re.sub(r'\btrue\b', 'True', s)
        s = re.sub(r'\bfalse\b', 'False', s)
        s = re.sub(r'\bnull\b', 'None', s)
        
        start = s.find('{')
        end = s.rfind('}')
        if start != -1 and end != -1:
            result = ast.literal_eval(s[start:end+1])
            if isinstance(result, dict):
                logger.debug("Parsed using ast.literal_eval")
                return result
    except Exception:
        pass
    
    logger.error("JSON parse error, could not extract valid JSON")
    logger.warning(f"Raw response (first 800 chars): {response[:800]}")
    return {}


def _fix_escaped_values(obj: Any, key: str = None) -> Any:
    """
    递归修复字典和列表中的转义字符
    
    注意：对于 'code' 字段，不处理转义，因为代码中的 \\n 是有意义的转义序列
    
    Args:
        obj: 要处理的对象（字典、列表、字符串或其他）
        key: 当前键名，用于判断是否为代码字段
        
    Returns:
        修复后的对象
    """
    if isinstance(obj, dict):
        return {k: _fix_escaped_values(v, key=k) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_fix_escaped_values(item, key=key) for item in obj]
    elif isinstance(obj, str):
        # 对于代码字段，不进行转义处理
        # 因为代码中的 \n 应该保持为 \n（两个字符），而不是真正的换行
        if key in ('code', 'fixed_code', 'revised_content'):
            return obj
        
        # 对于其他字段，修复过度转义的换行符
        result = obj
        result = result.replace('\\\\n', '\n')
        result = result.replace('\\n', '\n')
        result = result.replace('\\\\r', '\r')
        result = result.replace('\\r', '\r')
        result = result.replace('\\\\t', '\t')
        result = result.replace('\\t', '\t')
        return result
    else:
        return obj


class JSONParser:
    """
    JSON解析器类（面向对象封装版本）
    
    如果需要在类中使用这些方法，可以继承此类或实例化使用
    
    Examples:
        >>> parser = JSONParser()
        >>> result = parser.parse('{"name": "test"}')
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        return parse_json_response(response)
    
    def fix_escaped_values(self, obj: Any, key: str = None) -> Any:
        """修复转义字符"""
        return _fix_escaped_values(obj, key)


# 导出接口
__all__ = ['parse_json_response', '_fix_escaped_values', 'JSONParser']


if __name__ == '__main__':
    # 测试示例
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试1: markdown代码块
    test1 = '```json\n{"name": "test", "value": 123}\n```'
    print("Test 1:", parse_json_response(test1))
    
    # 测试2: 代码字段保护
    test2 = '{"code": "print(\\"hello\\nworld\\")"}'
    print("Test 2:", parse_json_response(test2))
    
    # 测试3: 多层转义
    test3 = '{"text": "line1\\\\nline2"}'
    print("Test 3:", parse_json_response(test3))
