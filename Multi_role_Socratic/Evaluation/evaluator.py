'''
负责评估模型的结果:正确率、平均时间等统计。
不关心对话过程，也不直接调用模型，只关心输入的真实答案和模型预测结果的对比。'''

import time
from typing import List, Dict, Any

class Evaluator:
    def __init__(self):
        self.total = 0
        self.correct = 0
        self.details = []

    def update_record(self, question: str, dialogue: List[Dict[str, str]], success: bool, elapsed: float):
        self.total += 1
        if success:
            self.correct += 1
        self.details.append({
            "question": question,
            "dialogue": dialogue,
            "success": success,
            "time": elapsed
        })

    def summary(self) -> Dict[str, float]:
        accuracy = self.correct / self.total if self.total > 0 else 0.0
        avg_time = sum(d["time"] for d in self.details) / self.total if self.total > 0 else 0.0
        return {
            "total_questions": self.total,
            "correct_answers": self.correct,
            "accuracy": accuracy,
            "average_time": avg_time
        }


    def evaluate_single_model_on_dataset(self,model, dataset: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        使用model对dataset做单独调用测试，返回 {"accuracy": ..., "total":..., ...}。
        model: 可以是TeacherModel或StudentModel实例
        dataset: [{"question":..., "answer":..., ...}, ...]
        """
        correct = 0
        total = 0
        total_time = 0.0

        for idx, item in enumerate(dataset):
            question = item["question"]
            true_answer = float(item["answer"])  # 假设你的答案可转成float

            start_t = time.time()
            # 1) 单独获取模型答案（不走对话流程）
            answer_text = model.get_single_answer(question)
            # 2) 解析数值预测
            pred_answer = model.extract_pred_answer(answer_text)
            elapsed = time.time() - start_t
            total_time += elapsed

            # 3) 判断对错
            total += 1
            if pred_answer is not None and abs(pred_answer - true_answer) < 1e-6:
                correct += 1

        accuracy = correct / total if total > 0 else 0
        return {
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "average_time": total_time / total if total > 0 else 0
        }

