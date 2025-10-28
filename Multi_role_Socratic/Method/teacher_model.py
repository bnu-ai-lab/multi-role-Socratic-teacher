"""
修改老师模型的时候要注意修改self.config中名称  TEACHER_API_KEY,TEACHER_API_BASE等
"""
import re
import time
from typing import List, Dict
from openai import OpenAI  # 仅示例，按你的实际API import
from config import TEACHER_CONFIG,DEEPSEEK_API_KEY
TEACHER_API_KEY=DEEPSEEK_API_KEY
TEACHER_API_BASE ="https://api.deepseek.com"


# OPENAI_API_KEY='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'
# TEACHER_API_KEY=OPENAI_API_KEY
# TEACHER_API_BASE='https://api.openai.com/v1'
# TEACHER_MODEL_NAME="gpt-4o-mini"
class TeacherModel:
    def __init__(self):
        # 初始化教师客户端
        self.teacher_client = OpenAI(api_key=TEACHER_API_KEY, base_url=TEACHER_API_BASE)
        
        #self.config = TEACHER_CONFIG
        self.config = {
                "model": "deepseek-chat" ,  # 修改模型名称
                "temperature": 0.8,
                "max_tokens": 128
            }

    def call_teacher(self, messages: List[Dict[str, str]], retries: int = 3) -> str:
        """
        多轮对话中调用教师模型并返回结果
        """
        for attempt in range(retries):
            try:
                response = self.teacher_client.chat.completions.create(
                    model=self.config["model"],
                    messages=messages,
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return ""  # 理论上不会到这里
    
    def get_single_answer(self, question: str) -> str:
        """
       单独调用教师模型，给出单纯的答案。
        """
        messages = [
            {"role": "system", "content": "You're a math problem solver."},
            {
                "role": "user", 
                "content": (
                    "Please analyze and solve the following problem step by step:\n"
                    f"{question}\n"
                    "Note: answer in the form of 'FinalAnswer:XX' or '\\boxed{XX}'."
                )
            }
        ]
        return self.call_teacher(messages)

    def extract_pred_answer(self, answer_text: str) -> float:
        """
        解析逻辑:
        - 优先匹配FinalAnswer:XX或\boxed{XX}
        - 否则尝试提取最后一个数字
        """
        # 示例：先匹配 \boxed{XX}
        final_boxed = re.search(r'\\boxed\{(\d+(\.\d+)?)\}', answer_text)
        if final_boxed:
            return float(final_boxed.group(1))
        
        # 再匹配 FinalAnswer:
        final_answer = re.search(r'FinalAnswer:\s*(\d+(\.\d+)?)', answer_text)
        if final_answer:
            return float(final_answer.group(1))

        # 如果还没有，就提取最后一个数字
        numbers = re.findall(r'\d+(\.\d+)?', answer_text)
        if numbers:
            last_number = numbers[-1]
            if isinstance(last_number, tuple):
                last_number = ''.join(last_number)
            return float(last_number) if last_number else None
        return None
