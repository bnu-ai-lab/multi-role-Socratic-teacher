"""
封装调用“学生模型”的接口
对外提供调用学生模型的方法
"""
import re
import time
from typing import List, Dict
from openai import OpenAI  # 仅示例，按你的实际API import
from config import STUDENT_API_KEY, STUDENT_API_BASE, STUDENT_CONFIG


class StudentModel:
    def __init__(self):
        # 初始化学生客户端
        self.student_client = OpenAI(api_key=STUDENT_API_KEY, base_url=STUDENT_API_BASE)
        self.config = STUDENT_CONFIG

    def call_student(self, messages: List[Dict[str, str]], retries: int = 3) -> str:
        """
        多轮对话中调用学生模型并返回结果
        """
        for attempt in range(retries):
            try:
                response = self.student_client.chat.completions.create(
                    model=self.config["model"],
                    messages=messages,
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"],
                    timeout=60
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"学生模型调用失败: {str(e)}")
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return ""
    
    def get_single_answer(self, question: str) -> str:
        """
        单独调用学生模型，得到答案。
        """
        messages = [
            {"role": "system", "content": "你是一个数学问题解决助手。"},
            {
                "role": "user",
                "content": (
                    f"think about the following question:\n{question}\n"
                    "and answer in the form of 'FinalAnswer:XX'."
                )
            }
        ]
        return self.call_student(messages)

    def extract_pred_answer(self, answer_text: str) -> float:
        """
        单独针对学生模型的答案提取逻辑
        """
        final_answer = re.search(r'FinalAnswer:\s*(\d+(\.\d+)?)', answer_text)
        if final_answer:
            return float(final_answer.group(1))

        numbers = re.findall(r'\d+(\.\d+)?', answer_text)
        if numbers:
            last_number = numbers[-1]
            if isinstance(last_number, tuple):
                last_number = ''.join(last_number)
            return float(last_number) if last_number else None
        return None
