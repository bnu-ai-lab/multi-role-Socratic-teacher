import os


MAX_STEPS = 10 

# local teacher
TEACHER_CONFIG = {
    "model": "0",  
    "temperature": 0.8,
    "max_tokens": 256
}


STUDENT_CONFIG = {
    "model": "Pro/Qwen/Qwen2.5-7B-Instruct",  
    "temperature": 0.5,
    "max_tokens": 1024
}

STUDENT_API_KEY = "sk-safogzaicxxtvgkuwaxrahcomzbvzgxuobmsawglq"
STUDENT_API_BASE = "https://api.siliconflow.cn/v1"

# local 
TEACHER_API_KEY = "0" 
TEACHER_API_BASE = "http://127.0.0.1:30000/v1"

DEEPSEEK_API_KEY = "sk-8bd54031a4592b489340ba64"
DEEPSEEK_URl = 'https://api.deepseek.com'


OPENAI_API_KEY='sk-5atcO66hhYnUvnETJZ8pLz6lhj4tj4RymWQ'

