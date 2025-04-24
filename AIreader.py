from pathlib import Path
import json
import time
import requests
from openai import OpenAI

# 加载配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 初始化API客户端
client = OpenAI(
    api_key=config["moonshot_api_key"],
    base_url="https://api.moonshot.cn/v1",
)

# 设置目录路径
pdf_dir = Path(config["pdf_dir"])
output_dir = Path(config["output_dir"])

# EasyDoc API配置
EASYDOC_API_KEY = config["easydoc_api_key"]
EASYDOC_PARSE_URL = "https://api.easydoc.sh/api/v1/parse"
EASYDOC_RESULT_URL = "https://api.easydoc.sh/api/v1/parse/{task_id}/result"


#——————————————————————————— 主程序 ——————————————————————————————

output_dir.mkdir(exist_ok=True)
prompt = """
# Role: 文献结构化摘要专家

## Profile
- language: 中文
- description: 专门为管理学与统计学领域文献提供结构化摘要服务，生成符合学术规范的Obsidian笔记
- background: 具有管理学博士学位和统计学专业背景，熟悉学术写作规范
- personality: 严谨、细致、追求精确
- expertise: 文献分析、知识图谱构建、学术写作
- target_audience: 管理学研究者、学术工作者、知识管理实践者

## Skills

1. 文献分析技能
   - 主题识别: 准确提取文献核心主题和研究问题
   - 理论映射: 梳理理论发展脉络和相互关系
   - 方法评估: 分析研究设计和统计方法的适切性
   - 结论提炼: 精炼核心发现和学术贡献

2. 知识管理技能
   - 结构化组织: 按标准模板组织信息
   - 语义标注: 添加适当的标签和链接
   - 交叉引用: 建立文献间的关联关系
   - 格式优化: 适配Obsidian的Markdown语法

## Rules

1. 学术规范原则：
   - 准确性: 严格忠实原文，不添加个人臆测
   - 完整性: 覆盖研究背景、方法、结果等关键要素
   - 客观性: 保持中立立场，避免价值判断
   - 可追溯性: 标明所有引用来源的具体页码

2. 输出质量标准：
   - 结构化: 严格遵循指定模板的层级结构
   - 专业性: 使用学科规范术语
   - 简洁性: 去除冗余信息，突出关键内容
   - 互操作性: 确保与Obsidian的知识图谱功能兼容

3. 限制条件：
   - 不扩展原文未明确包含的内容
   - 不改变作者原意
   - 不使用非学术性语言
   - 不省略关键方法论细节

## Workflows

- 目标: 生成可直接导入Obsidian的结构化文献笔记，标题设置为文章标题
- 步骤 1: 提取文献元数据(标题、作者、期刊等)
- 步骤 2: 分析并结构化核心内容
- 步骤 3: 添加语义标签和内部链接
- 步骤 4: 按模板格式化输出
- 预期结果: 完整、准确、可直接使用的文献笔记

## OutputFormat

1. Markdown格式：
   - format: markdown
   - structure: 包含标题、元数据、摘要、核心观点等8个标准部分
   - style: 学术严谨，段落分明
   - special_requirements: 支持Obsidian的双向链接语法

2. 格式规范：
   - indentation: 使用统一的缩进层级
   - sections: 明确的二级标题分隔
   - highlighting: 关键术语用**加粗**强调

3. 验证规则：
   - validation: 检查各部分完整性
   - constraints: 不超过2000字
   - error_handling: 缺失部分明确标注"待补充"

4. 示例说明：
   1. 示例1：
      - 标题: 管理学文献笔记
      - 格式类型: Markdown
      - 说明: 完整展示各部分的连接方式
      - 示例内容: |
          # 文献标题

          #管理 #理论 #方法论  

          **作者:**  
          **期刊:**  
          **发表时间:**  

          ## 摘要：
          [150字左右的精要概述]

          ## 研究背景：
          [研究问题的起源和学术价值]

          ## 核心观点：
          - 观点1  
          - 观点2  

          ## 文献综述：
          理论发展脉络 [[相关文献1]] [[相关文献2]]

          ## 研究方法：
          [研究设计、数据来源、分析方法]

          ## 总结与展望：
          [主要结论和未来研究方向]

## Initialization
作为文献结构化摘要专家，你必须遵守上述Rules，按照Workflows执行任务，并按照Markdown格式输出，在展示核理理论框架时可以使用mermaid图表和latex公式。
"""

# 使用EasyDoc解析PDF
def parse_pdf_with_easydoc(pdf_file):
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 上传文件并获取task_id
            with open(pdf_file, 'rb') as f:
                files = {'file': f}
                data = {'mode': 'premium'}
                headers = {'api-key': EASYDOC_API_KEY}
                
                response = requests.post(EASYDOC_PARSE_URL, headers=headers, files=files, data=data)
                print(f"EasyDoc API响应状态码: {response.status_code}")
                print(f"EasyDoc API响应内容: {response.text}")
                
                task_id = response.json().get("data", {}).get("task_id")
                
                if not task_id:
                    raise Exception(f"Failed to get task_id, API响应: {response.text}")
                
                # 获取解析结果
                result_url = EASYDOC_RESULT_URL.format(task_id=task_id)
                response = requests.get(result_url, headers=headers)
                print(f"EasyDoc结果API响应状态码: {response.status_code}")
                print(f"EasyDoc结果API响应内容: {response.text}")
                json_data = response.json()
                
                # 构建树形结构并转换为文本
                nodes = json_data.get("data", {}).get("task_result", {}).get("nodes", [])
                tree = build_tree(nodes)
                return tree_flat(tree)
                
        except Exception as e:
            retry_count += 1
            print(f"解析失败({retry_count}/{max_retries}): {e}")
            if retry_count >= max_retries:
                return None
            time.sleep(30)

# EasyDoc树形结构处理函数
def rule(node, depth):
    txt = ""
    if node["type"] == "Text":
        txt = node["text"]
    elif node["type"] == "Title":
        title_level = "#" * depth
        txt = f"{title_level} {node['text']}"
    elif node["type"] in ("Table", "Figure"):
        txt = f"""\n```{"table" if node["type"] == "Table" else "figure"}\n"""
        txt += node.get("vlm_understanding", node["text"]) + "\n```\n"
    return f"\n{txt}\n"


def tree_flat(tree, depth=1):
    rst = ""
    for node in tree:
        rst += rule(node, depth)
        if node.get("type") == "Title":
            rst += tree_flat(node["children"], depth + 1)
    return rst


def build_tree(nodes, parent_id=-1):
    tree = []
    for node in nodes:
        if node["parent_id"] == parent_id:
            children = build_tree(nodes, node["id"])
            node["children"] = children
            tree.append(node)
    return tree


# 与AI对话并保存结果
def chat_with_ai(content, output_file):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "system", "content": content},
        {"role": "user", "content": "请形成文献笔记"},
    ]
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            completion = client.chat.completions.create(
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
                print(f"速率限制触发({retry_count}/{max_retries})，跳过文件: {e}")
                return False
            print(f"请求失败({retry_count}/{max_retries}): {e}")
            if retry_count >= max_retries:
                return False
            time.sleep(30)

# 调用 DeepSeek API
def call_deepseek(content, output_file):
    API_ENDPOINT = "https://api.siliconflow.cn/v1/chat/completions"
    API_KEY = config["siliconflow_key"]
    max_retries = 5
    retry_count = 0

    headers = {
        "Authorization": f"Bearer {API_KEY}",
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
            {"role": "system", "content": prompt},
            {"role": "system", "content": content},
            {"role": "user", "content": "请形成文献笔记"}
        ]
    }

    while retry_count < max_retries:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        if response.status_code == 200:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.json()["choices"][0]["message"]["content"])
            return True
        elif response.status_code == 429:
            print(f"速率限制触发({retry_count}/{max_retries})，跳过文件: {response.json()}")
            return False
        elif response.status_code == 20042:
            print(f"检测到特殊错误码20042({retry_count}/{max_retries})，将转为使用月之暗面API处理")
            return False
        else:
            retry_count += 1
            print(f"请求失败({retry_count}/{max_retries}): {response.json()}")
            if retry_count >= max_retries:
                return False
            time.sleep(30)


import os
import json

# 在output_dir定义后添加
processed_file = output_dir / "processed_files.json"

# 主程序部分修改为
failed_files = []
processed_files = []

# 加载已处理文件列表
if processed_file.exists():
    with open(processed_file, 'r') as f:
        processed_files = json.load(f)

for pdf_file in pdf_dir.glob("*.pdf"):
    if pdf_file.name in processed_files:
        print(f"跳过已处理文件: {pdf_file.name}")
        continue
        
    print(f"正在处理文件: {pdf_file.name}")
    output_file = output_dir / f"{pdf_file.stem}.md"
    
    try:
        # 使用EasyDoc解析PDF
        print("使用EasyDoc解析PDF文件")
        text_content = parse_pdf_with_easydoc(pdf_file)
        
        if text_content:
            # 调用AI生成文献笔记
            if not call_deepseek(text_content, output_file):
                failed_files.append(pdf_file.name)
        else:
            failed_files.append(pdf_file.name)
            
        # 处理成功则记录
        processed_files.append(pdf_file.name)
        with open(processed_file, 'w') as f:
            json.dump(processed_files, f)
            
    except Exception as e:
        print(f"处理文件 {pdf_file.name} 时出错: {e}")
        failed_files.append(pdf_file.name)
    
    time.sleep(30)  # 每次请求后等待 30 秒，避免触发速率限制

# 输出失败文件列表
if failed_files:
    print("\n以下文件处理失败：")
    for file in failed_files:
        print(f"- {file}")
else:
    print("所有文件处理完成！")
