import time
from openai import OpenAI

class KimiGenerator:
    def __init__(self, api_key, base_url, prompt):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.prompt = prompt

    def generate_note(self, content, output_file):
        max_retries = 5
        retry_count = 0
        
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "system", "content": content},
            {"role": "user", "content": "请形成文献笔记"},
        ]
        
        while retry_count < max_retries:
            try:
                completion = self.client.chat.completions.create(
                    model="moonshot-v1-128k",
                    messages=messages,
                    temperature=0.3,
                )
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(completion.choices[0].message.content)
                return True
            except Exception as e:
                retry_count += 1
                if hasattr(e, 'status_code') and e.status_code == 429:
                    return False
                if retry_count >= max_retries:
                    return False
                time.sleep(30)