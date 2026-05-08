"""
递归下降语法分析器实现
基于LL(1)文法的预测分析法
"""

from typing import List, Optional
from my_token import Token, TokenType
from ast_node import ASTNode, ParseError
from lexer import tokenize


class EduParser:
    """EduAssist反馈格式的递归下降语法分析器"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self._enable_extensions = False  # 扩展特性开关
    
    def enable_extensions(self, enable: bool = True):
        """启用扩展特性（容错支持）"""
        self._enable_extensions = enable
    
    def peek(self) -> Token:
        """查看当前Token但不消费"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, '', 0, 0)
    
    def peek_type(self) -> TokenType:
        """查看当前Token类型"""
        return self.peek().type
    
    def peek_value(self) -> str:
        """查看当前Token的值"""
        return self.peek().value
    
    def consume(self, expected_type: TokenType) -> Token:
        """消费一个指定类型的Token，如果类型不匹配则抛出异常"""
        token = self.peek()
        
        if token.type == expected_type:
            self.pos += 1
            return token
        
        # 启用扩展模式时的容错处理
        if self._enable_extensions:
            # 尝试修复常见错误
            fixed = self._try_fix_token(expected_type, token)
            if fixed:
                return fixed
        
        raise ParseError(
            position=self.pos,
            expected=expected_type.name,
            found=token.type.name,
            message=f"Expected {expected_type.name}, found {token.type.name} at line {token.line}"
        )
    
    def _try_fix_token(self, expected: TokenType, actual: Token) -> Optional[Token]:
        """
        扩展模式：尝试修复Token错误
        返回修复后的Token，如果无法修复则返回None
        """
        # 修复1: 缺少分号时自动插入
        if expected == TokenType.SEMICOLON and actual.type != TokenType.SEMICOLON:
            # 检查是否在SCORE字段后缺少分号
            if hasattr(self, '_last_was_score') and self._last_was_score:
                print(f"[Fix] Auto-inserting missing semicolon at position {self.pos}")
                return Token(TokenType.SEMICOLON, ';', actual.line, actual.column)
        
        return None
    
    def _at_end(self) -> bool:
        """检查是否到达Token列表末尾"""
        return self.pos >= len(self.tokens) or self.peek_type() == TokenType.EOF
    
    # ==================== 解析函数 ====================
    
    def parse_feedback(self) -> ASTNode:
        """
        Feedback → KEYWORD_FEEDBACK LBRACE FieldList RBRACE
        """
        node = ASTNode("Feedback")
        
        # 消费 FEEDBACK
        self.consume(TokenType.KEYWORD_FEEDBACK)
        
        # 消费 {
        self.consume(TokenType.LBRACE)
        
        # 解析字段列表
        node.add_child(self.parse_field_list())
        
        # 消费 }
        self.consume(TokenType.RBRACE)
        
        return node
    
    def parse_field_list(self) -> ASTNode:
        """
        FieldList → Field FieldList | ε
        注意：字段顺序固定为 SCORE, LEVEL, COMMENT, ERRORS
        """
        node = ASTNode("FieldList")
        
        # 检查是否有更多字段
        if self._at_end():
            return node
        
        # 根据下一个Token决定是否继续解析
        if self.peek_type() in [TokenType.KEYWORD_SCORE, TokenType.KEYWORD_LEVEL,
                                 TokenType.KEYWORD_COMMENT, TokenType.KEYWORD_ERRORS]:
            # 解析第一个字段
            node.add_child(self.parse_field())
            
            # 递归解析剩余字段
            remaining = self.parse_field_list()
            for child in remaining.children:
                node.add_child(child)
        
        return node
    
    def parse_field(self) -> ASTNode:
        """
        Field → ScoreField | LevelField | CommentBlock | ErrorList
        
        根据当前Token的前瞻来判断解析哪个字段
        """
        token_type = self.peek_type()
        
        if token_type == TokenType.KEYWORD_SCORE:
            return self.parse_score_field()
        elif token_type == TokenType.KEYWORD_LEVEL:
            return self.parse_level_field()
        elif token_type == TokenType.KEYWORD_COMMENT:
            return self.parse_comment_block()
        elif token_type == TokenType.KEYWORD_ERRORS:
            return self.parse_error_list()
        else:
            raise ParseError(
                position=self.pos,
                expected="SCORE, LEVEL, COMMENT or ERRORS",
                found=token_type.name,
                message=f"Unexpected token at start of field"
            )
    
    def parse_score_field(self) -> ASTNode:
        """
        ScoreField → KEYWORD_SCORE COLON NUMBER SEMICOLON
        """
        node = ASTNode("ScoreField")
        
        # 消费 SCORE
        self.consume(TokenType.KEYWORD_SCORE)
        
        # 消费 :
        self.consume(TokenType.COLON)
        
        # 消费 NUMBER
        num_token = self.consume(TokenType.NUMBER)
        node.value = int(num_token.value)
        
        # 标记用于容错
        self._last_was_score = True
        
        # 消费 ;
        try:
            self.consume(TokenType.SEMICOLON)
        except ParseError as e:
            if self._enable_extensions:
                # 扩展模式：自动插入分号
                print(f"[Warning] {e}, auto-inserting semicolon")
                self._last_was_score = False
            else:
                raise
        
        self._last_was_score = False
        
        return node
    
    def parse_level_field(self) -> ASTNode:
        """
        LevelField → KEYWORD_LEVEL COLON IDENT SEMICOLON
        """
        node = ASTNode("LevelField")
        
        # 消费 LEVEL
        self.consume(TokenType.KEYWORD_LEVEL)
        
        # 消费 :
        self.consume(TokenType.COLON)
        
        # 消费 IDENT (medium, high, low等)
        ident_token = self.consume(TokenType.IDENT)
        node.value = ident_token.value
        
        # 消费 ;
        self.consume(TokenType.SEMICOLON)
        
        return node
    
    def parse_comment_block(self) -> ASTNode:
        """
        CommentBlock → KEYWORD_COMMENT LBRACE CommentContent RBRACE
        CommentContent → TEXTField SuggestionField
        TEXTField → KEYWORD_TEXT COLON STRING SEMICOLON
        SuggestionField → KEYWORD_SUGGESTION COLON STRING SEMICOLON
        """
        node = ASTNode("CommentBlock")
        
        # 消费 COMMENT
        self.consume(TokenType.KEYWORD_COMMENT)
        
        # 消费 {
        self.consume(TokenType.LBRACE)
        
        # 解析 TEXT 字段
        text_node = self.parse_text_field()
        node.add_child(text_node)
        
        # 解析 SUGGESTION 字段
        suggestion_node = self.parse_suggestion_field()
        node.add_child(suggestion_node)
        
        # 消费 }
        self.consume(TokenType.RBRACE)
        
        return node
    
    def parse_text_field(self) -> ASTNode:
        """
        TEXTField → KEYWORD_TEXT COLON STRING SEMICOLON
        """
        node = ASTNode("TextField")
        
        # 消费 TEXT
        self.consume(TokenType.KEYWORD_TEXT)
        
        # 消费 :
        self.consume(TokenType.COLON)
        
        # 消费 STRING
        str_token = self.consume(TokenType.STRING)
        # 去除引号
        node.value = str_token.value[1:-1] if str_token.value.startswith('"') else str_token.value
        
        # 消费 ;
        self.consume(TokenType.SEMICOLON)
        
        return node
    
    def parse_suggestion_field(self) -> ASTNode:
        """
        SuggestionField → KEYWORD_SUGGESTION COLON STRING SEMICOLON
        """
        node = ASTNode("SuggestionField")
        
        # 消费 SUGGESTION
        self.consume(TokenType.KEYWORD_SUGGESTION)
        
        # 消费 :
        self.consume(TokenType.COLON)
        
        # 消费 STRING
        str_token = self.consume(TokenType.STRING)
        node.value = str_token.value[1:-1] if str_token.value.startswith('"') else str_token.value
        
        # 消费 ;
        self.consume(TokenType.SEMICOLON)
        
        return node
    
    def parse_error_list(self) -> ASTNode:
        """
        ErrorList → KEYWORD_ERRORS LBRACKET ErrorItems RBRACKET
        ErrorItems → ErrorItem ErrorItems | ε
        ErrorItem → KEYWORD_ERROR LPAREN ErrorParams RPAREN SEMICOLON
        ErrorParams → ParamList
        ParamList → Param COMMA ParamList | Param
        Param → line: NUMBER | type: IDENT | msg: STRING
        """
        node = ASTNode("ErrorList")
        
        # 消费 ERRORS
        self.consume(TokenType.KEYWORD_ERRORS)
        
        # 消费 [
        self.consume(TokenType.LBRACKET)
        
        # 解析错误项列表（可以为空）
        error_items_node = self.parse_error_items()
        for child in error_items_node.children:
            node.add_child(child)
        
        # 消费 ]
        self.consume(TokenType.RBRACKET)
        
        return node
    
    def parse_error_items(self) -> ASTNode:
        """
        ErrorItems → ErrorItem ErrorItems | ε
        """
        node = ASTNode("ErrorItems")
        
        # 检查是否还有错误项
        if self._at_end():
            return node
        
        # 如果下一个Token是ERROR，继续解析
        if self.peek_type() == TokenType.KEYWORD_ERROR:
            node.add_child(self.parse_error_item())
            
            # 递归解析剩余错误项
            remaining = self.parse_error_items()
            for child in remaining.children:
                node.add_child(child)
        
        return node
    
    def parse_error_item(self) -> ASTNode:
        """
        ErrorItem → KEYWORD_ERROR LPAREN ErrorParams RPAREN SEMICOLON
        """
        node = ASTNode("ErrorItem")
        
        # 消费 ERROR
        self.consume(TokenType.KEYWORD_ERROR)
        
        # 消费 (
        self.consume(TokenType.LPAREN)
        
        # 解析参数列表
        params_node = self.parse_error_params()
        node.add_child(params_node)
        
        # 消费 )
        self.consume(TokenType.RPAREN)
        
        # 消费 ;
        self.consume(TokenType.SEMICOLON)
        
        return node
    
    def parse_error_params(self) -> ASTNode:
        """
        ErrorParams → ParamList
        ParamList → Param COMMA ParamList | Param
        """
        node = ASTNode("ErrorParams")
        
        # 解析第一个参数
        node.add_child(self.parse_param())
        
        # 可能有更多参数
        while self.peek_type() == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            node.add_child(self.parse_param())
        
        return node
    
    def parse_param(self) -> ASTNode:
        """
        Param → line: NUMBER | type: IDENT | msg: STRING
        """
        # 解析参数名
        name_token = self.consume(TokenType.IDENT)
        param_name = name_token.value
        
        # 消费 :
        self.consume(TokenType.COLON)
        
        # 根据参数名解析对应的值
        if param_name == "line":
            value_token = self.consume(TokenType.NUMBER)
            node = ASTNode("LineParam", value=int(value_token.value))
        elif param_name == "type":
            value_token = self.consume(TokenType.IDENT)
            node = ASTNode("TypeParam", value=value_token.value)
        elif param_name == "msg":
            value_token = self.consume(TokenType.STRING)
            node = ASTNode("MsgParam", value=value_token.value[1:-1])
        else:
            raise ParseError(
                position=self.pos,
                expected="line, type or msg",
                found=param_name,
                message=f"Unknown parameter name: {param_name}"
            )
        
        return node
    
    def parse(self) -> ASTNode:
        """主解析入口"""
        result = self.parse_feedback()
        
        # 确保解析完所有Token
        if not self._at_end() and self.peek_type() != TokenType.EOF:
            raise ParseError(
                position=self.pos,
                message=f"Unexpected tokens after parsing: {self.peek().type.name}"
            )
        
        return result


def parse_text(text: str, enable_extensions: bool = False) -> ASTNode:
    """便捷函数：解析反馈文本"""
    tokens = tokenize(text)
    parser = EduParser(tokens)
    if enable_extensions:
        parser.enable_extensions(True)
    return parser.parse()


def extract_feedback_data(ast: ASTNode) -> dict:
    result = {
        "score": None,
        "level": None,
        "comment": None,
        "suggestion": None,
        "errors": []
    }
    
    for child in ast.children:
        if child.node_type == "FieldList":
            for field in child.children:
                if field.node_type == "ScoreField":
                    result["score"] = field.value
                elif field.node_type == "LevelField":
                    result["level"] = field.value
                elif field.node_type == "CommentBlock":
                    for comment_child in field.children:
                        if comment_child.node_type == "TextField":
                            result["comment"] = comment_child.value
                        elif comment_child.node_type == "SuggestionField":
                            result["suggestion"] = comment_child.value
                elif field.node_type == "ErrorList":
                    # 遍历 ErrorList 的子节点
                    for error_item in field.children:
                        if error_item.node_type == "ErrorItem":
                            error_data = {}
                            # 遍历 ErrorItem 的子节点（ErrorParams）
                            for param_container in error_item.children:
                                if param_container.node_type == "ErrorParams":
                                    # 遍历各个参数
                                    for param in param_container.children:
                                        if param.node_type == "LineParam":
                                            error_data["line"] = param.value
                                        elif param.node_type == "TypeParam":
                                            error_data["type"] = param.value
                                        elif param.node_type == "MsgParam":
                                            error_data["msg"] = param.value
                            if error_data:
                                result["errors"].append(error_data)
                    # 也检查 ErrorItems 节点
                    for error_items in field.children:
                        if error_items.node_type == "ErrorItems":
                            for error_item in error_items.children:
                                if error_item.node_type == "ErrorItem":
                                    error_data = {}
                                    for param_container in error_item.children:
                                        if param_container.node_type == "ErrorParams":
                                            for param in param_container.children:
                                                if param.node_type == "LineParam":
                                                    error_data["line"] = param.value
                                                elif param.node_type == "TypeParam":
                                                    error_data["type"] = param.value
                                                elif param.node_type == "MsgParam":
                                                    error_data["msg"] = param.value
                                    if error_data:
                                        result["errors"].append(error_data)
    
    return result