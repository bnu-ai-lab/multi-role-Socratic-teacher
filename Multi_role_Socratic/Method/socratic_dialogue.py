'''
核心的“苏格拉底对话”过程。
使用 TeacherModel 与 StudentModel 的实例完成教师-学生的交互逻辑。
对话结束后，产出对话记录以及模型预测结果等信息。
'''
import re
import time
from typing import List, Dict, Tuple
from Method.teacher_model import TeacherModel
from Method.student_model import StudentModel

from openai import OpenAI
from Datasets.dataset_config import DATASET_STRATEGY
from config import TEACHER_CONFIG, STUDENT_CONFIG, MAX_STEPS


class SocraticDialogue:
    def __init__(self):
        self.teacher_model = TeacherModel()
        self.student_model = StudentModel()

    def validate_dialogue_structure(self, history: List[Dict[str, str]]) -> bool:
        """验证交替对话结构，仅示例，可根据需要扩展"""
        for i in range(0, len(history), 2):
            if history[i]["role"] != "assistant":
                return False
            if i + 1 < len(history) and history[i + 1]["role"] != "user":
                return False
        return True

    def run_dialogue(
        self,
        question: str,
        analysis: str,
        true_answer,
        dataset_name: str  # gsm8k / math
    ) -> Tuple[bool, List[dict]]:
        """
        执行苏格拉底对话
        """
        # 从 DATASET_STRATEGY 中拿到对应函数和Prompt
        strategy = DATASET_STRATEGY[dataset_name]

        extract_answer_fn = strategy["extract_answer_fn"]
        is_equiv_fn = strategy["is_equiv_fn"]

        teacher_history = strategy["get_teacher_history"](question, true_answer, analysis)
        student_history = strategy["get_student_history"](question)

        MIN_TURNS_BEFORE_CHECK = 5
        dialogue_record = []
        #MAX_STEPS:每个STEP里老师和学生都发言一次
        for step in range(MAX_STEPS):
            # 1) 老师先说
            teacher_msg = self.teacher_model.call_teacher(teacher_history)
            teacher_history.append({"role": "assistant", "content": teacher_msg})
            student_history.append({"role": "user", "content": teacher_msg})
            dialogue_record.append({"role": "assistant", "content": teacher_msg})

            # 2) 学生回复
            student_msg = self.student_model.call_student(student_history)
            student_history.append({"role": "assistant", "content": student_msg})
            teacher_history.append({"role": "user", "content": student_msg})
            dialogue_record.append({"role": "user", "content": student_msg})

            # 3) 从学生回复提取答案，看是否已给FinalAnswer或\boxed等
            # step 从0开始计数, step+1为第几轮(每轮是“老师+学生”)
            # if step + 1 >= MIN_TURNS_BEFORE_CHECK:
                # 3.1) 提取答案
            pred_answer = extract_answer_fn(student_msg)
            if pred_answer is not None:
                        # 3.2) 对比真答案
                correct = is_equiv_fn(pred_answer, true_answer)
                return (correct, dialogue_record)
            
        # 若循环结束仍未返回，则表示没触发 final answer
        return (False, dialogue_record)


