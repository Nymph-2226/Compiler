# EduAssist 反馈语法分析器

## 项目简介

本项目是编译原理课程作业，实现了一个面向教育场景的大模型输出语法分析器。系统能够：

- 解析LLM生成的格式化反馈文本
- 构建抽象语法树(AST)
- 提取结构化的反馈数据(分数、等级、评语、建议、错误列表)
- 支持与DeepSeek API对接，实现端到端的作业批改评价

## 文件结构
Compiler/
├── ast_node.py # AST节点定义
├── my_token.py # Token类型定义
├── lexer.py # 词法分析器
├── parser.py # 递归下降语法分析器
├── evaluate.py # 端到端评估脚本（集成LLM API）
├── test_direct.py # 直接解析测试脚本
├── test_cases.py # 测试用例批量运行脚本
├── test_cases/ # 测试用例目录
│ ├── correct_feedback.txt # 正确输入1
│ ├── correct_feedback2.txt # 正确输入2
│ ├── invalid_missing_brace.txt # 语法错误（缺少括号）
│ ├── invalid_wrong_keyword.txt # 语法错误（错误关键字）
│ └── llm_real_output.txt # LLM真实输出
└── README.md # 运行说明

## 环境要求

- Python 3.8+
- requests库（仅真实API模式需要）

## 依赖安装命令

pip install requests
API密钥配置方式

方式一：环境变量（推荐）
Windows PowerShell:

$env:LLM_API_KEY = "your-deepseek-api-key"
$env:LLM_API_BASE_URL = "https://api.deepseek.com/v1"
$env:LLM_MODEL = "deepseek-chat"
$env:LLM_PROVIDER = "deepseek"
Linux/Mac:

export LLM_API_KEY="your-deepseek-api-key"
export LLM_API_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"
export LLM_PROVIDER="deepseek"

方式二：永久配置（Windows）
打开"系统属性" → "环境变量"
新建用户变量：
变量名：LLM_API_KEY，变量值：你的API Key
变量名：LLM_API_BASE_URL，变量值：https://api.deepseek.com/v1
变量名：LLM_MODEL，变量值：deepseek-chat
变量名：LLM_PROVIDER，变量值：deepseek

获取API Key
访问 https://platform.deepseek.com/
注册账号并登录
进入"API Keys"页面
点击"Create API Key"
复制保存生成的Key

如何运行各任务
任务一：文法设计与LL(1)分析表构造
本任务为理论设计，无需运行代码。相关设计内容参见实验报告。

任务二：递归下降语法分析器实现
2.1 测试AST结构输出（截图位置1）

python test_direct.py
2.2 测试5个测试用例

python test_cases.py
预期输出：
correct_feedback.txt → ✅ 解析成功
correct_feedback2.txt → ✅ 解析成功
invalid_missing_brace.txt → ❌ 解析失败（预期）
invalid_wrong_keyword.txt → ❌ 解析失败（预期）
llm_real_output.txt → ⚠️ 需预处理

任务三：接入大语言模型API
3.1 模拟测试（不调用真实API）

python evaluate.py --mode mock
3.2 真实API测试（截图位置3）

# 先配置API密钥（见上方说明）
$env:LLM_API_KEY = "your-api-key"

# 运行真实API测试
python evaluate.py --mode real
预期输出：
============================================================
运行真实API测试
============================================================
API Provider: deepseek
API Model: deepseek-chat

测试: correct_code
----------------------------------------
分数: 95
等级: high
解析成功: True

统计: {'total_attempts': 2, 'parse_success': 2, 'success_rate': 1.0}
其他命令
单个文件解析测试

python -c "from parser import parse_text; print(parse_text(open('test_cases/correct_feedback.txt', encoding='utf-8').read()).pprint())"
调试API输出

python debug.py
文法定义
text
Feedback         → FEEDBACK LBRACE FieldList RBRACE
FieldList        → Field FieldList | ε
Field            → ScoreField | LevelField | CommentBlock | ErrorList
ScoreField       → SCORE COLON NUMBER SEMICOLON
LevelField       → LEVEL COLON IDENT SEMICOLON
CommentBlock     → COMMENT LBRACE CommentContent RBRACE
CommentContent   → TextField SuggestionField
TextField        → TEXT COLON STRING SEMICOLON
SuggestionField  → SUGGESTION COLON STRING SEMICOLON
ErrorList        → ERRORS LBRACKET ErrorItems RBRACKET
ErrorItems       → ErrorItem ErrorItems | ε
ErrorItem        → ERROR LPAREN ErrorParams RPAREN SEMICOLON
ErrorParams      → ParamList
ParamList        → Param COMMA ParamList | Param
Param            → line COLON NUMBER | type COLON IDENT | msg COLON STRING
输出示例
AST结构
text
Feedback
  FieldList
    ScoreField: 85
    LevelField: medium
    CommentBlock
      TextField: 代码逻辑清晰，但边界处理不足
      SuggestionField: 增加空指针检查
    ErrorList
      ErrorItem
        ErrorParams
          LineParam: 12
          TypeParam: runtime
          MsgParam: NullPointerException
提取的JSON数据
json
{
  "score": 85,
  "level": "medium",
  "comment": "代码逻辑清晰，但边界处理不足",
  "suggestion": "增加空指针检查",
  "errors": [
    {"line": 12, "type": "runtime", "msg": "NullPointerException"}
  ]
}
扩展特性
启用扩展模式后，解析器支持：

SCORE字段省略分号：自动补全缺失的分号

ERROR参数顺序容错：允许line、type、msg以任意顺序出现

测试结果汇总
测试文件	类型	结果
correct_feedback.txt	正确输入	✅ 解析成功
correct_feedback2.txt	正确输入	✅ 解析成功
invalid_missing_brace.txt	语法错误	❌ 解析失败（预期）
invalid_wrong_keyword.txt	语法错误	❌ 解析失败（预期）
llm_real_output.txt	LLM真实输出	⚠️ 需预处理提取FEEDBACK块
常见问题
Q1: 运行test_cases.py时出现编码错误？
# 重新生成测试文件
python recreate_testcases.py

Q2: 真实API调用返回402错误？
DeepSeek账户余额不足，需要充值。访问 https://platform.deepseek.com/ 充值。

Q3: 解析失败怎么办？
启用扩展模式：在代码中设置 enable_extensions=True
检查LLM输出格式是否符合文法定义
查看错误信息定位问题位置

Q4: 如何验证LL(1)条件？
本文法满足LL(1)条件：
无左递归
已提取公共左因子
FIRST(A) ∩ FOLLOW(A) = ∅（对含ε产生式的非终结符）

作者信息
课程：编译原理
作业：语法分析专题
GitHub名：Nymph-2226