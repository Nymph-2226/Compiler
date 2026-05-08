"""
Token类型定义模块
"""

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Token类型枚举"""
    # 关键字
    KEYWORD_FEEDBACK = auto()
    KEYWORD_SCORE = auto()
    KEYWORD_LEVEL = auto()
    KEYWORD_COMMENT = auto()
    KEYWORD_TEXT = auto()
    KEYWORD_SUGGESTION = auto()
    KEYWORD_ERRORS = auto()
    KEYWORD_ERROR = auto()
    
    # 分隔符
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    COLON = auto()       # :
    SEMICOLON = auto()   # ;
    COMMA = auto()       # ,
    
    # 字面量
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()
    
    # 特殊
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """Token数据结构"""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', line={self.line})"