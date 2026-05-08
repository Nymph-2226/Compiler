"""
词法分析器实现
根据作业给定的Token定义实现
"""

import re
from typing import List, Generator
from my_token import Token, TokenType


class Lexer:
    """词法分析器"""
    
    # Token模式定义（按优先级排序）
    token_patterns = [
        # 关键字 - 使用负向前瞻确保不匹配更长单词的一部分
        (r'FEEDBACK\b', TokenType.KEYWORD_FEEDBACK),
        (r'SCORE\b', TokenType.KEYWORD_SCORE),
        (r'LEVEL\b', TokenType.KEYWORD_LEVEL),
        (r'COMMENT\b', TokenType.KEYWORD_COMMENT),
        (r'TEXT\b', TokenType.KEYWORD_TEXT),
        (r'SUGGESTION\b', TokenType.KEYWORD_SUGGESTION),
        (r'ERRORS\b', TokenType.KEYWORD_ERRORS),
        (r'ERROR\b', TokenType.KEYWORD_ERROR),
        
        # 分隔符
        (r'\{', TokenType.LBRACE),
        (r'\}', TokenType.RBRACE),
        (r'\[', TokenType.LBRACKET),
        (r'\]', TokenType.RBRACKET),
        (r'\(', TokenType.LPAREN),
        (r'\)', TokenType.RPAREN),
        (r':', TokenType.COLON),
        (r';', TokenType.SEMICOLON),
        (r',', TokenType.COMMA),
        
        # 字符串（支持中文和转义）
        (r'"(?:[^"\\]|\\.)*"', TokenType.STRING),
        
        # 数字
        (r'\d+', TokenType.NUMBER),
        
        # 标识符（小写字母开头，用于medium, runtime, logic等）
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENT),
        
        # 跳过空白字符
        (r'\s+', None),
        
        # 单行注释
        (r'//[^\n]*', None),
    ]
    
    def __init__(self, text: str):
        self.text = text
        self.line = 1
        self.col = 1
        self.pos = 0
        self.tokens = []
    
    def tokenize(self) -> List[Token]:
        """执行词法分析，返回Token列表"""
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.col = 1
        
        while self.pos < len(self.text):
            matched = False
            
            for pattern, token_type in self.token_patterns:
                regex = re.compile(pattern)
                match = regex.match(self.text, self.pos)
                
                if match:
                    matched = True
                    value = match.group(0)
                    start_pos = self.pos
                    self.pos = match.end()
                    
                    # 更新行列信息
                    # 计算匹配文本中的换行数
                    lines_in_match = value.count('\n')
                    if lines_in_match > 0:
                        self.line += lines_in_match
                        last_newline_pos = value.rfind('\n')
                        self.col = len(value) - last_newline_pos
                    else:
                        self.col += len(value)
                    
                    # 如果token_type为None，跳过（如空白字符）
                    if token_type is not None:
                        token = Token(token_type, value, self.line, self.col - len(value))
                        self.tokens.append(token)
                    
                    break
            
            if not matched:
                # 无法匹配的字符
                error_char = self.text[self.pos]
                token = Token(TokenType.ERROR, error_char, self.line, self.col)
                self.tokens.append(token)
                self.pos += 1
                self.col += 1
        
        # 添加EOF标记
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        
        return self.tokens
    
    def get_tokens(self) -> List[Token]:
        """返回Token列表（别名）"""
        return self.tokenize()
    
    def __repr__(self):
        return f"Lexer(text='{self.text[:50]}...')"


def tokenize(text: str) -> List[Token]:
    """便捷函数：对文本进行词法分析"""
    lexer = Lexer(text)
    return lexer.tokenize()