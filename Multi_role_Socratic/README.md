## Quick run

```shell
启动老师模型
conda activate lsh-api

CUDA_VISIBLE_DEVICES=0 API_PORT=8002 llamafactory-cli api --model_name_or_path /home/ubuntu/lsh/project/Socratic/Model/SocraticLM --template qwen --trust_remote_code

python -m sglang.launch_server --model-path /home/ubuntu/lsh/project/Socratic/Model/SocraticLM --port 30000 --attention-backend triton --schedule-conservativeness 0.1

CUDA_VISIBLE_DEVICES=0 API_PORT=8002 llamafactory-cli api \
    --model_name_or_path /home/ubuntu/lsh/project/Socratic/Model/Qwen2___5-Math-7B-Instruct \
    --adapter_name_or_path /home/ubuntu/lsh/project/new_work/outputs/SocraticLM/saves_round2 \
    --template qwen \
    --trust_remote_code



python -m sglang.launch_server \
  --model-path /home/ubuntu/lsh/project/new_work/outputs/SocraticLM-R/full_qwen2_lora_merged \
  --port 30000 \
  --attention-backend triton \
  --schedule-conservativeness 0.1

```
```shell
运行脚本
conda activate lsh_socratic
python main.py 
```


增加数据集需要修改：
在dataset_config.py--DATASET_STRATEGY中添加对应的prompt，答案提前函数，答案匹配函数

