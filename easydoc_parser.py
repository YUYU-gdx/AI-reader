import json
import time
import requests
from pathlib import Path

class EasyDocParser:
    def __init__(self, api_key, pdf_dir, output_dir):
        self.api_key = api_key
        self.parse_url = "https://api.easydoc.sh/api/v1/parse"
        self.result_url = "https://api.easydoc.sh/api/v1/parse/{task_id}/result"
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.md_output_dir = self.output_dir / "markdown_output"
        self.md_output_dir.mkdir(exist_ok=True)
        self.json_output_dir = self.output_dir / "json_output"
        self.json_output_dir.mkdir(exist_ok=True)

    def parse_pdf(self, pdf_file):
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"尝试解析PDF: {pdf_file.name} (尝试 {retry_count+1}/{max_retries})")
                with open(pdf_file, 'rb') as f:
                    files = {'file': f}
                    data = {'mode': 'lite'}
                    headers = {'api-key': self.api_key}
                    
                    response = requests.post(self.parse_url, headers=headers, files=files, data=data)
                    print(f"API响应状态码: {response.status_code}")
                    
                    if response.status_code != 200:
                        print(f"API错误响应: {response.text}")
                        raise Exception(f"API请求失败: {response.status_code}")
                    
                    response_json = response.json()
                    task_id = response_json.get("data", {}).get("task_id")
                    
                    if not task_id:
                        raise Exception("无法从响应中获取task_id")
                    
                    result_url = self.result_url.format(task_id=task_id)
                    response = requests.get(result_url, headers=headers)
                    json_data = response.json()
                                        
                    json_file = self.json_output_dir / f"{pdf_file.stem}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)

                    blocks = json_data.get("data", {}).get("task_result", {}).get("blocks", [])
                    markdown_content = self._format_blocks(blocks)
                    
                    # 新增：保存markdown文件
                    md_file = self.md_output_dir / f"{pdf_file.stem}.md"
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    return markdown_content
                    
            except Exception as e:
                retry_count += 1
                print(f"解析失败: {str(e)}")
                if retry_count >= max_retries:
                    return None
                time.sleep(30)

    def _format_blocks(self, blocks):
        markdown = ""
        for block in blocks:
            if block["type"] == "Title":
                markdown += f"\n# {block['text']}\n"
            elif block["type"] == "Text":
                markdown += f"\n{block['text']}\n"
            elif block["type"] in ("Table", "Figure"):
                markdown += f"\n```{block['type'].lower()}\n{block.get('text', '')}\n```\n"
        return markdown