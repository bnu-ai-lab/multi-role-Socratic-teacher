"""
ulity to handle google style math datasets such as MATH
"""
import re
import json


def save_df_to_json(df, filename):
    # 将 DataFrame 转换为字典列表
    records = df.to_dict(orient='records')
    # 将字典列表保存为易于阅读的 JSON 文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)  # indent=4 可确保 JSON 文件格式化输出
    print(f"DataFrame 已成功保存为 {filename} 文件。")

##从字符串中提取最后一个\boxed{}或\fbox{}中的内容。
def last_boxed_only_string(string):
    idx = string.rfind("\\boxed")
    if idx < 0:
        idx = string.rfind("\\fbox")
        if idx < 0:
            return PARSERFAILD

    i = idx
    right_brace_idx = None
    num_left_braces_open = 0
    while i < len(string):
        if string[i] == "{":
            num_left_braces_open += 1
        if string[i] == "}":
            num_left_braces_open -= 1
            if num_left_braces_open == 0:
                right_brace_idx = i
                break
        i += 1
    
    if right_brace_idx == None:
        retval = PARSERFAILD
    else:
        retval = string[idx:right_brace_idx + 1]
    
    return retval
##去除字符串中的\boxed{}，只保留其中的内容。
def remove_boxed(s):
    left = "\\boxed{"
    try:
        assert s[:len(left)] == left
        assert s[-1] == "}"
        return s[len(left):-1]
    except:
        return PARSERFAILD

def get_pure_anwer(str):
    retval = last_boxed_only_string(str)
    return remove_boxed(retval)

#修复分数
def _fix_fracs(string):
    substrs = string.split("\\frac")
    new_str = substrs[0]
    if len(substrs) > 1:
        substrs = substrs[1:]
        for substr in substrs:
            new_str += "\\frac"
            if substr[0] == "{":
                new_str += substr
            else:
                try:
                    assert len(substr) >= 2
                except:
                    return string
                a = substr[0]
                b = substr[1]
                if b != "{":
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}{" + b + "}" + post_substr
                    else:
                        new_str += "{" + a + "}{" + b + "}"
                else:
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}" + b + post_substr
                    else:
                        new_str += "{" + a + "}" + b
    string = new_str
    return string

#将a/b格式的字符串转换为\frac{a}{b}
def _fix_a_slash_b(string):
    if len(string.split("/")) != 2:
        return string
    a = string.split("/")[0]
    b = string.split("/")[1]
    try:
        a = int(a)
        b = int(b)
        assert string == "{}/{}".format(a, b)
        new_string = "\\frac{" + str(a) + "}{" + str(b) + "}"
        return new_string
    except:
        return string
#去除右侧单位
def _remove_right_units(string):
    # "\\text{ " only ever occurs (at least in the val set) when describing units
    if "\\text{ " in string:
        splits = string.split("\\text{ ")
        assert len(splits) == 2
        return splits[0]
    else:
        return string

#修复sqrt
def _fix_sqrt(string):
    if "\\sqrt" not in string:
        return string
    splits = string.split("\\sqrt")
    new_string = splits[0] 
    for split in splits[1:]:
        if split[0] != "{":
            a = split[0]
            new_substr = "\\sqrt{" + a + "}" + split[1:]
        else:
            new_substr = "\\sqrt" + split
        new_string += new_substr
    return new_string

#总提纯函数
def _strip_string(string):
    # linebreaks  
    string = string.replace("\n", "")
    #print(string)

    # remove inverse spaces
    string = string.replace("\\!", "")
    #print(string)

    # replace \\ with \
    string = string.replace("\\\\", "\\")
    #print(string)

    # replace tfrac and dfrac with frac
    string = string.replace("tfrac", "frac")
    string = string.replace("dfrac", "frac")
    #print(string)

    # remove \left and \right
    string = string.replace("\\left", "")
    string = string.replace("\\right", "")
    #print(string)
    
    # Remove circ (degrees)
    string = string.replace("^{\\circ}", "")
    string = string.replace("^\\circ", "")

    # remove dollar signs
    string = string.replace("\\$", "")
    
    # remove units (on the right)
    string = _remove_right_units(string)

    # remove percentage
    string = string.replace("\\%", "")
    string = string.replace("\%", "")

    # " 0." equivalent to " ." and "{0." equivalent to "{." Alternatively, add "0" if "." is the start of the string
    string = string.replace(" .", " 0.")
    string = string.replace("{.", "{0.")
    # if empty, return empty string
    if len(string) == 0:
        return string
    if string[0] == ".":
        string = "0" + string

    # to consider: get rid of e.g. "k = " or "q = " at beginning
    if len(string.split("=")) == 2:
        if len(string.split("=")[0]) <= 2:
            string = string.split("=")[1]

    # fix sqrt3 --> sqrt{3}
    string = _fix_sqrt(string)

    # remove spaces
    string = string.replace(" ", "")

    # \frac1b or \frac12 --> \frac{1}{b} and \frac{1}{2}, etc. Even works with \frac1{72} (but not \frac{72}1). Also does a/b --> \\frac{a}{b}
    string = _fix_fracs(string)

    # manually change 0.5 --> \frac{1}{2}
    if string == "0.5":
        string = "\\frac{1}{2}"

    # NOTE: X/Y changed to \frac{X}{Y} in dataset, but in simple cases fix in case the model output is X/Y
    string = _fix_a_slash_b(string)

    return string




# check the box answer is right,对两个字符串进行提纯，然后比较它们是否相等。
def is_equiv_math(str1, str2, verbose=False):
    if str1 is None and str2 is None:
        print("WARNING: Both None")
        return True
    if str1 is None or str2 is None:
        return False

    try:
        ss1 = _strip_string(str1)
        ss2 = _strip_string(str2)
        if verbose:
            print(ss1, ss2)
        return ss1 == ss2
    except:
        return str1 == str2
    
# check the box answer is right
def is_equiv_gsm8k(str1, str2):
    # 确保 str2 转换为 float 类型，以便进行比较
    if isinstance(str2, str):
        str2 = str2.strip()  # 去除字符串两端的空格，防止比较时的问题
        try:
            str2 = float(str2)  # 尝试将字符串转换为 float
        except ValueError:
            return False  # 如果转换失败，直接返回 False

    # 如果 str2 是 int 或 float，直接使用它
    if isinstance(str2, int) or isinstance(str2, float):
        # 将 str1 转换为 float 比较
        try:
            str1 = float(str1)  # 转换 str1 为 float
        except ValueError:
            return False  # 如果转换失败，返回 False

    # 比较转换后的两个数值，容忍浮动误差（比如浮点数精度问题）
    if abs(str1 - str2) < 1e-9:  # 你可以根据需要调整误差范围
        return True
    else:
        return False
    
def parser_one_answer_aqua(predicted_answer):
    """
    Extracts the pure answer from a raw predicted answer.

    Args:
        predicted_answer (str): Raw answer returned by an LLM.

    Returns:
        str: Parsed answer if successful, or 'PARSERFAILD' otherwise.
    """
    # 检测\boxed里面的内容，因为prompt里面叫llm把答案写成 \boxed{answer}
    match1 = re.search(r'\\boxed{(.*?)}', predicted_answer)
    # 从后往前匹配 A，B，C，D，E，F 其中任何一个
    match2 = list(re.finditer(r'(A|B|C|D|E|F)', predicted_answer))
    if match1:
        result = match1.group(1)
        if result.isalpha() and result.isupper() and len(result) == 1:
            return result
        else:
            return PARSERFAILD  # 不是大写字母，返回解析失败
    elif match2:
        return match2[-1].group(1)
    else:
        # 都不成功，返回 PARSERFAILD,标记解析失败
        return PARSERFAILD 

def parser_one_answer_gsm8k_math(pure_predicted_answer):
    return get_pure_anwer(pure_predicted_answer)


# dataset config
#["aqua" , "gsm8k" , "math"]
end_prompt_aqua = "Explain your reasoning. Your final answer should be a single uppercase letter , in the form \boxed{answer}, at the end of your response."
end_prompt_gsm8k_math = """Explain your reasoning. Your final answer should in the form \boxed{answer}, at the end of your response.\n
attention the response answer format
Q: The angle measures of the three angles of a triangle are in the ratio $1:3:6$. What is the number of degrees in the measure of the largest angle?\n
A: Because the angle measures are in the ratio $1:3:6$, the angle measures are $x$, $3x$, and $6x$ for some value of $x$.  Because the angles of a triangle add to $180^\\circ$, we have $x+3x+6x = 180^\\circ$, so $10x = 180^\\circ$ and $x =18^\\circ$.  Therefore, the largest angle has measure $6x = \\boxed{108^\\circ}$.
Q:
"""

DatasetConfig = {
    "aqua": (
        lambda x, y: x == y,    # equivalence_check
        parser_one_answer_aqua, # parser
        end_prompt_aqua         # end_prompt
    ),
    "gsm-8k": (
        is_equiv_gsm8k,         # equivalence_check
        parser_one_answer_gsm8k_math, # parser
        end_prompt_gsm8k_math   # end_prompt
    ),
    "Math": (
        is_equiv_math,          # equivalence_check
        parser_one_answer_gsm8k_math, # parser
        end_prompt_gsm8k_math   # end_prompt
    ),
    "math-alg":(
        is_equiv_math,          # equivalence_check
        parser_one_answer_gsm8k_math, # parser
        end_prompt_gsm8k_math   # end_prompt
    )
}

import concurrent.futures  
import time  
import json  
from tenacity import retry, stop_after_attempt, wait_fixed  

def process_data_parallel(
    data,
    process_item_fn,
    output_file_path = None,
    chunk_size=256,
    max_workers=16,
    retry_params=None,
    sleep_time= 100,
):
    """
    通用工具函数，用于以并行方式分块处理数据。

    参数：
        data (list): 待处理数据列表。
        process_item_fn (function): 单个数据项的处理函数。
        output_file_path (str): 结果输出文件路径。
        chunk_size (int): 每块包含的数据数量。
        max_workers (int): 并行处理时的最大工作线程数。
        retry_params (dict, optional): 可选的重试参数，包含"stop"和"wait"。
        sleep_time (float): 处理每个块后的休眠时间。
    """
    retry_params = retry_params or {"stop": stop_after_attempt(3), "wait": wait_fixed(61)}

    @retry(stop=retry_params["stop"], wait=retry_params["wait"])
    def process_with_retry(item):
        return process_item_fn(item)

    def process_chunk(chunk):
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            processed_items = list(executor.map(process_with_retry, chunk))
        return [item for item in processed_items if item is not None]

    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    processed_data = []

    for idx, chunk in enumerate(chunks):
        print(f"Processing chunk {idx + 1}/{len(chunks)}...")
        processed_chunk = process_chunk(chunk)
        processed_data.extend(processed_chunk)
        print(f"sleep{sleep_time}")
        time.sleep(sleep_time)

    if output_file_path != None:
        with open(output_file_path, 'w') as f:
            json.dump(processed_data, f, indent=4)
        print(f"Data processing complete. Results saved to {output_file_path}")

    print(f"finish all the thing !")
    return processed_data
