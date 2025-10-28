'''
加载数据集、循环调用对话方法、记录日志、进行评估、输出最终结果。
需修改：json_filename,text_filename
'''
import time
import threading
import os
import json
from typing import List, Dict
from Datasets.dataset_loader import DatasetLoader
from Method.socratic_dialogue import SocraticDialogue
from Evaluation.evaluator import Evaluator
from Output.logger_refine import DialogueLogger
from Method.teacher_model import TeacherModel
from Method.student_model import StudentModel
from config import GSM8K_DATASET_PATH, MATH_DATASET_PATH, TEST_DATASET_PATH, LOG_DIR
from ulity import process_data_parallel

max_workers = 24

class ThreadSafeEvaluator:
    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator
        self.lock = threading.Lock()
        self.processed_count = 0  # 用于显示进度的计数

    def update_record(self, *args, **kwargs):
        with self.lock:
            self.processed_count += 1
            return self.evaluator.update_record(*args, **kwargs)

    def summary(self):
        with self.lock:
            return self.evaluator.summary()

    def get_processed_count(self):
        with self.lock:
            return self.processed_count

def main():
    print(f"max_workers: {max_workers}")
    dataset_name = "math"  # 或者 "gsm8k"
    current_method = "deepseek"  # 当前这一轮要跑的方法
    methods = ["standerd", "socraticLM", "socraticLM-R", "deepseek"]

    # 1. 初始化各模块
    dialogue_runner = SocraticDialogue()
    base_eval = Evaluator()
    evaluator = ThreadSafeEvaluator(base_eval)

    # 日志文件在 LOG_DIR 下
    json_filename = "dialogue_deepseek_math_7.30.json"
    text_filename = "dialogue_deepseek_math_7.30.log"
    logger = DialogueLogger(log_dir=LOG_DIR, json_filename=json_filename,text_filename=text_filename)

    # 2. 加载数据集
    loader = DatasetLoader(gsm8k_path=GSM8K_DATASET_PATH, math_path=MATH_DATASET_PATH, test_path=TEST_DATASET_PATH)
    dataset = loader.load_dataset(dataset_name=dataset_name)
    json_path = os.path.join(LOG_DIR, json_filename)

    # 2.1 若日志不存在则初始化，否则使用现有
    if not os.path.exists(json_path):
        print(f"{json_path} 不存在，开始初始化日志文件...")
        # questions_list = [item["question"] for item in dataset]
        # logger.initialize_log_file(questions_list, methods)
        logger.initialize_log_file(dataset, methods)
    else:
        print(f"检测到已存在日志文件：{json_path}，跳过初始化。")

    # 2.2 读取日志，获取 checkpoint
    with open(json_path, "r", encoding="utf-8") as f:
        log_data = json.load(f)

    # ========== 第一步： 回放 已完成题目到 Evaluator，以便正确率统计 ========== #
    def replay_completed_for_accuracy(evaluator: Evaluator, log_data: List[Dict], method_name: str):
        """
        对当前方法 method_name，回放此前已完成 (checkpoint=true) 且 result[method_name] = "正确" 或 "错误" 的题目，
        使得 Evaluator 的 total/correct 同样包括这些题。
        """
        done_cnt = 0
        correct_cnt = 0
        for entry in log_data:
            if entry["checkpoint"] is True:
                result_str = entry["result"].get(method_name, "")
                if result_str in ["正确", "错误"]:
                    success = (result_str == "正确")
                    done_cnt += 1
                    if success:
                        correct_cnt += 1
                    # 伪对话
                    pseudo_dialogue = [{"role": "assistant", "content": "这是回放的对话"}]
                    # 时间先设 0.0 或其他
                    evaluator.update_record(entry["question"], pseudo_dialogue, success, 0.0)
        print(f"回放已完成题目 => {done_cnt} 道记录纳入Evaluator，其中 {correct_cnt} 道正确.")

    # 调用回放函数, 仅对 current_method
    replay_completed_for_accuracy(base_eval, log_data, current_method)

    # ========== 第二步：只处理 checkpoint=false 的题目 ========== #
    checkpoint_map = {entry["question"]: entry["checkpoint"] for entry in log_data}
    items_to_process = [it for it in dataset if not checkpoint_map.get(it["question"], False)]
    already_done_count = len(dataset) - len(items_to_process)

    print(f"共有 {len(dataset)} 道题，其中 {len(items_to_process)} 道未完成 (checkpoint=false), "
          f"{already_done_count} 道已完成. 本轮将处理这些未完成的.")

    # 让 evaluator.processed_count = already_done_count
    with evaluator.lock:
        evaluator.processed_count = already_done_count

    # 3. 定义并行处理函数
    def process_item(item):
        question = item["question"]
        analysis = item["analysis"]
        true_answer = item["answer"]
        try:
            start_time = time.time()
            success, dialogue = dialogue_runner.run_dialogue(question, analysis, true_answer, dataset_name)
            elapsed = time.time() - start_time

            # (1) Evaluator 记录(线程安全)
            evaluator.update_record(question, dialogue, success, elapsed)
            # (2) 写纯文本日志
            logger.log_dialogue_text(question, dialogue, success)
            # (3) 写JSON日志 => checkpoint=true
            logger.update_method_dialogue(question, current_method, dialogue, success)

            # 打印进度 & 准确率
            with threading.Lock():
                processed = evaluator.get_processed_count()
                acc = evaluator.summary()["accuracy"]
                total = len(dataset)
                print(f"进度: {processed}/{total} | 当前正确率: {acc:.2%}")

            return {"question": question, "success": success, "elapsed": elapsed}

        except Exception as e:
            # 出错时不更新日志 => checkpoint 仍是 false
            print(f"[Error]处理题目({question})时出现异常: {e}")
            return None

    # 4. 并行处理 items_to_process
    results = process_data_parallel(
        data=items_to_process,
        process_item_fn=process_item,
        chunk_size=256,
        max_workers=max_workers
    )

    # 5. 最终结果
    final_report = evaluator.summary()
    print("\n==== 最终结果 ====")
    print(f"总题数: {final_report['total_questions']}")
    print(f"正确数: {final_report['correct_answers']}")
    print(f"准确率: {final_report['accuracy']:.2%}")
    print(f"平均响应时间: {final_report['average_time']:.2f} 秒/题")

if __name__ == "__main__":
    main()
