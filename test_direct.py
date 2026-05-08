"""
直接测试解析器 - 不调用API
"""

from parser import parse_text, extract_feedback_data

# 测试输入
test_feedback = '''
FEEDBACK {
    SCORE: 85;
    LEVEL: medium;
    COMMENT {
        TEXT: "代码逻辑清晰，但边界处理不足";
        SUGGESTION: "增加空指针检查";
    }
    ERRORS [
        ERROR(line:12, type:runtime, msg:"NullPointerException");
        ERROR(line:27, type:logic, msg:"边界条件错误");
    ]
}
'''

print("=" * 50)
print("测试解析器")
print("=" * 50)

# 解析
ast = parse_text(test_feedback)

print("\nAST结构:")
print(ast.pprint())

# 提取数据
data = extract_feedback_data(ast)

print("\n提取的数据:")
print(f"  分数: {data['score']}")
print(f"  等级: {data['level']}")
print(f"  评语: {data['comment']}")
print(f"  建议: {data['suggestion']}")
print(f"  错误列表:")
for err in data['errors']:
    print(f"    - 行{err.get('line')}: {err.get('type')} - {err.get('msg')}")