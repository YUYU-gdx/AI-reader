import json
import time
import requests

class DeepSeekGenerator:
    def __init__(self, api_key, prompt):
        self.api_endpoint = "https://api.siliconflow.cn/v1/chat/completions"
        self.api_key = api_key
        self.prompt = prompt

    def generate_note(self, content, output_file):
        max_retries = 5
        retry_count = 0

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "stream": False,
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "stop": [],
            "messages": [
                {"role": "system", "content": self.prompt},
                {"role": "system", "content": content},
                {"role": "user", "content": "请形成文献笔记"}
            ]
        }

        while retry_count < max_retries:
            response = requests.post(self.api_endpoint, json=payload, headers=headers)
            if response.status_code == 200:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(response.json()["choices"][0]["message"]["content"])
                return True
            elif response.status_code == 429:
                print(f"速率限制触发: {response.json().get('message', '未知错误')}")  // 添加详细错误信息
                return False
            elif response.status_code == 20042:
                print(f"特殊错误: {response.json().get('message', '未知错误')}")  // 添加详细错误信息
                return False
            else:
                print(f"请求失败(状态码 {response.status_code}): {response.text}")  // 打印完整响应
                retry_count += 1
                if retry_count >= max_retries:
                    return False
                time.sleep(30)