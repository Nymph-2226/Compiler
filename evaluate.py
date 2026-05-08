"""
端到端评估脚本
集成LLM API调用、语法解析、结果提取
"""

import os
import json
import time
from typing import Dict, Tuple

# 导入自定义模块
from lexer import tokenize
from parser import EduParser, parse_text, extract_feedback_data
from ast_node import ParseError

# 尝试导入requests
try:
    import requests
except ImportError:
    print("错误: 请先安装requests库: pip install requests")
    exit(1)


# ==================== 配置 ====================

class LLMProvider:
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    ZHIPU = "zhipu"


API_KEY = os.environ.get("LLM_API_KEY", "")
API_BASE_URL = os.environ.get("LLM_API_BASE_URL", "https://api.openai.com/v1")
API_MODEL = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
API_PROVIDER = os.environ.get("LLM_PROVIDER", LLMProvider.OPENAI)


# ==================== Prompt模板 ====================

SYSTEM_PROMPT = """
你是一个编程课程的AI助教，专门负责批改学生的编程作业。

你必须严格按照以下格式输出批改反馈：

FEEDBACK {
    SCORE: <0-100的数字>;
    LEVEL: <low/medium/high>;
    COMMENT {
        TEXT: "<评语>";
        SUGGESTION: "<建议>";
    }
    ERRORS [
        ERROR(line:<行号>, type:<syntax/runtime/logic>, msg:"<描述>");
    ]
}
"""


def build_user_prompt(code_snippet: str) -> str:
    prompt = '请批改以下学生代码，并按照指定格式输出反馈：\n\n'
    prompt += '```python\n'
    prompt += code_snippet + '\n'
    prompt += '```\n\n'
    prompt += '请分析代码的正确性、效率和代码质量。'
    return prompt


# ==================== LLM API调用 ====================

class LLMClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or API_KEY
        self.base_url = base_url or API_BASE_URL
        self.model = model or API_MODEL
        self.provider = API_PROVIDER
    
    def call(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        headers = {"Content-Type": "application/json"}
        
        if self.provider == LLMProvider.OPENAI:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == LLMProvider.DEEPSEEK:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == LLMProvider.QWEN:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == LLMProvider.ZHIPU:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 2000,
        }
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM API调用失败: {e}")
            raise
    
    def call_with_retry(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> Tuple[str, bool]:
        for attempt in range(max_retries):
            try:
                result = self.call(system_prompt, user_prompt)
                return result, True
            except Exception as e:
                print(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        return "", False


# ==================== 反馈解析器 ====================

class FeedbackParser:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.stats = {
            "total_attempts": 0,
            "parse_success": 0,
            "retry_success": 0,
            "retry_failed": 0
        }
    
    def evaluate_submission(self, code_snippet: str, enable_extensions: bool = True) -> Dict:
        self.stats["total_attempts"] += 1
        
        llm_output, success = self.llm_client.call_with_retry(
            SYSTEM_PROMPT, build_user_prompt(code_snippet)
        )
        
        if not success:
            return {
                "score": None,
                "level": None,
                "comment": "LLM API调用失败",
                "suggestion": "请检查网络连接和API配置",
                "errors": [],
                "parse_success": False,
                "raw_output": ""
            }
        
        parse_success, result, error_msg = self._parse_output(llm_output, enable_extensions)
        
        if parse_success:
            self.stats["parse_success"] += 1
            result["parse_success"] = True
            result["raw_output"] = llm_output
            return result
        
        print(f"解析失败: {error_msg}")
        
        correction_prompt = self._build_correction_prompt(error_msg, code_snippet)
        retry_output, retry_success = self.llm_client.call_with_retry(SYSTEM_PROMPT, correction_prompt)
        
        if retry_success:
            parse_success_retry, result_retry, _ = self._parse_output(retry_output, enable_extensions)
            if parse_success_retry:
                self.stats["retry_success"] += 1
                result_retry["parse_success"] = True
                result_retry["retry_used"] = True
                result_retry["raw_output"] = retry_output
                return result_retry
        
        self.stats["retry_failed"] += 1
        return {
            "score": None,
            "level": None,
            "comment": "解析失败 - 输出格式不符合要求",
            "suggestion": f"错误: {error_msg}",
            "errors": [],
            "parse_success": False,
            "raw_output": llm_output
        }
    
    def _build_correction_prompt(self, error_msg: str, code_snippet: str) -> str:
        prompt = '你的上一次输出格式不符合要求。\n\n'
        prompt += f'错误信息: {error_msg}\n\n'
        prompt += '请严格按照以下格式重新输出：\n'
        prompt += 'FEEDBACK {\n'
        prompt += '    SCORE: <数字>;\n'
        prompt += '    LEVEL: <low/medium/high>;\n'
        prompt += '    COMMENT {\n'
        prompt += '        TEXT: "<评语>";\n'
        prompt += '        SUGGESTION: "<建议>";\n'
        prompt += '    }\n'
        prompt += '    ERRORS [\n'
        prompt += '        ERROR(line:<数字>, type:<syntax/runtime/logic>, msg:"<描述>");\n'
        prompt += '    ]\n'
        prompt += '}\n\n'
        prompt += '请只输出反馈内容，不要有任何额外解释。\n\n'
        prompt += '原始代码是：\n'
        prompt += '```python\n'
        prompt += code_snippet + '\n'
        prompt += '```'
        return prompt
    
    def _parse_output(self, output: str, enable_extensions: bool) -> Tuple[bool, Dict, str]:
        try:
            # 找到 FEEDBACK 关键字的位置
            start_idx = output.find("FEEDBACK")
            if start_idx == -1:
                return False, {}, "未找到 FEEDBACK 关键字"
        
            # 找到匹配的结束括号
            brace_count = 0
            end_idx = start_idx
            found_feedback = False
        
            for i, ch in enumerate(output[start_idx:], start_idx):
                if ch == '{':
                    brace_count += 1
                    found_feedback = True
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0 and found_feedback:
                        end_idx = i + 1
                        break
        
            if end_idx <= start_idx:
                return False, {}, "无法找到完整的 FEEDBACK 块"
        
            # 提取 FEEDBACK 块
            feedback_text = output[start_idx:end_idx]
        
            # 预处理：处理空 ERRORS 列表的情况
            # 将 "ERRORS [ ];" 或 "ERRORS [];" 转换为 "ERRORS []"
            import re
            feedback_text = re.sub(r'ERRORS\s*\[\s*\]\s*;', 'ERRORS []', feedback_text)
            feedback_text = re.sub(r'ERRORS\s*\[\s*\]', 'ERRORS []', feedback_text)
        
            print(f"提取的反馈块:\n{feedback_text}")  # 调试用
        
            # 解析
            ast = parse_text(feedback_text, enable_extensions)
            result = extract_feedback_data(ast)
            return True, result, ""
        except ParseError as e:
            return False, {}, str(e)
        except Exception as e:
            return False, {}, str(e)
    
    def get_stats(self) -> Dict:
        success_rate = self.stats["parse_success"] / self.stats["total_attempts"] if self.stats["total_attempts"] > 0 else 0
        return {**self.stats, "success_rate": success_rate}


# ==================== 测试用例 ====================

TEST_CODE_SNIPPETS = [
    {
        "name": "correct_code",
        "code": '''
def factorial(n):
    if n < 0:
        raise ValueError("n不能为负数")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
'''
    },
    {
        "name": "buggy_code",
        "code": '''
def factorial(n):
    result = 1
    for i in range(1, n+1):
        result = result * i
    return result
'''
    }
]


def run_tests_with_mock():
    print("=" * 60)
    print("运行模拟测试（不调用真实API）")
    print("=" * 60)
    
    class MockLLMClient:
        def call_with_retry(self, system_prompt, user_prompt):
            mock_output = '''FEEDBACK {
    SCORE: 85;
    LEVEL: medium;
    COMMENT {
        TEXT: "代码逻辑清晰，但可以增加输入验证";
        SUGGESTION: "添加对负数的检查";
    }
    ERRORS [
        ERROR(line:3, type:logic, msg:"未处理负数输入");
    ]
}'''
            return mock_output, True
    
    parser = FeedbackParser(MockLLMClient())
    
    for test in TEST_CODE_SNIPPETS:
        print(f"\n测试: {test['name']}")
        print("-" * 40)
        result = parser.evaluate_submission(test['code'])
        print(f"分数: {result.get('score')}")
        print(f"等级: {result.get('level')}")
        print(f"评语: {result.get('comment')}")
        print(f"建议: {result.get('suggestion')}")
        print(f"错误: {result.get('errors')}")
        print(f"解析成功: {result.get('parse_success')}")
    
    print(f"\n统计: {parser.get_stats()}")


def run_tests_with_real_api():
    if not API_KEY:
        print("错误: 请设置环境变量 LLM_API_KEY")
        print("示例: export LLM_API_KEY='your-api-key'")
        return
    
    print("=" * 60)
    print("运行真实API测试")
    print("=" * 60)
    print(f"API Provider: {API_PROVIDER}")
    print(f"API Model: {API_MODEL}")
    print()
    
    llm_client = LLMClient()
    parser = FeedbackParser(llm_client)
    
    for test in TEST_CODE_SNIPPETS:
        print(f"\n测试: {test['name']}")
        print("-" * 40)
        result = parser.evaluate_submission(test['code'])
        print(f"分数: {result.get('score')}")
        print(f"等级: {result.get('level')}")
        print(f"解析成功: {result.get('parse_success')}")
    
    print(f"\n统计: {parser.get_stats()}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EduAssist 反馈解析器")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock",
                       help="运行模式: mock(模拟), real(真实API)")
    
    args = parser.parse_args()
    
    if args.mode == "real":
        run_tests_with_real_api()
    else:
        run_tests_with_mock()


if __name__ == "__main__":
    main()