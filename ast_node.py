"""
抽象语法树(AST)节点定义模块
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class ASTNode:
    """抽象语法树节点"""
    node_type: str
    value: Any = None
    children: List['ASTNode'] = field(default_factory=list)
    
    def add_child(self, child: 'ASTNode'):
        """添加子节点"""
        self.children.append(child)
    
    def pprint(self, indent: int = 0) -> str:
        """递归打印AST结构"""
        result = "  " * indent + self.node_type
        if self.value is not None:
            result += f": {self.value}"
        result += "\n"
        for child in self.children:
            result += child.pprint(indent + 1)
        return result
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "type": self.node_type,
        }
        if self.value is not None:
            result["value"] = self.value
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        return result


@dataclass
class ParseError(Exception):
    """语法解析错误异常"""
    position: int
    expected: Optional[str] = None
    found: Optional[str] = None
    message: Optional[str] = None
    
    def __str__(self):
        if self.message:
            return f"ParseError at position {self.position}: {self.message}"
        return f"ParseError at position {self.position}: Expected '{self.expected}', found '{self.found}'"