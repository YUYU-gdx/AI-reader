from pathlib import Path
import json
import time
import logging
from easydoc_parser import EasyDocParser
from deepseek_generator import DeepSeekGenerator
from kimi_generator import KimiGenerator

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_reader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    logger.info("开始加载配置文件config.json")
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("配置文件加载成功")
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        raise

def load_prompt():
    logger.info("开始加载提示词文件literature_summary_prompt.txt")
    try:
        with open('literature_summary_prompt.txt', 'r', encoding='utf-8') as f:
            prompt = f.read()
        logger.info("提示词文件加载成功")
        return prompt
    except Exception as e:
        logger.error(f"加载提示词文件失败: {str(e)}")
        raise

def main():
    try:
        config = load_config()
        prompt = load_prompt()

        logger.info("初始化各处理模块...")
        pdf_dir = Path(config["pdf_dir"])
        output_dir = Path(config["output_dir"])
        output_dir.mkdir(exist_ok=True)
        logger.info(f"PDF目录: {pdf_dir}, 输出目录: {output_dir}")

        easydoc_parser = EasyDocParser(
            api_key=config["easydoc_api_key"],
            pdf_dir=pdf_dir,
            output_dir=output_dir
        )
        deepseek_generator = DeepSeekGenerator(
            api_key=config["siliconflow_key"],
            prompt=prompt
        )
        kimi_generator = KimiGenerator(
            api_key=config["moonshot_api_key"],
            base_url="https://api.moonshot.cn/v1",
            prompt=prompt
        )

        processed_file = output_dir / "processed_files.json"
        failed_files = []
        processed_files = []

        if processed_file.exists():
            logger.info("加载已处理文件列表...")
            with open(processed_file, 'r') as f:
                processed_files = json.load(f)
            logger.info(f"已加载{len(processed_files)}个已处理文件")

        for pdf_file in pdf_dir.glob("*.pdf"):
            if pdf_file.name in processed_files:
                logger.info(f"跳过已处理文件: {pdf_file.name}")
                continue
                
            logger.info(f"开始处理文件: {pdf_file.name}")
            original_md_file = output_dir / f"original_{pdf_file.stem}.md"  # 修改为original_前缀
            note_md_file = output_dir / f"note_{pdf_file.stem}.md"  # 新增笔记文件
            
            try:
                logger.info("调用EasyDoc解析PDF...")
                markdown_content = easydoc_parser.parse_pdf(pdf_file)
                
                if markdown_content:
                    # 保存原始解析结果
                    with open(original_md_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    logger.info(f"原始Markdown文件已生成: {original_md_file}")
                    
                    logger.info("调用AI生成笔记...")
                    # 尝试使用DeepSeek生成笔记
                    if not deepseek_generator.generate_note(markdown_content, note_md_file):
                        logger.warning("DeepSeek生成失败，尝试使用Kimi...")
                        # 如果DeepSeek失败，尝试使用Kimi
                        if not kimi_generator.generate_note(markdown_content, note_md_file):
                            logger.error("所有AI生成笔记失败")
                            failed_files.append(pdf_file.name)
                    else:
                        logger.info(f"笔记已生成: {note_md_file}")
                else:
                    logger.error("PDF解析失败，返回空内容")
                    failed_files.append(pdf_file.name)
                    
                processed_files.append(pdf_file.name)
                with open(processed_file, 'w') as f:
                    json.dump(processed_files, f)
                    
            except Exception as e:
                logger.error(f"处理文件 {pdf_file.name} 时出错: {str(e)}", exc_info=True)
                failed_files.append(pdf_file.name)
            
            time.sleep(30)

        if failed_files:
            logger.error(f"\n以下{len(failed_files)}个文件处理失败：")
            for file in failed_files:
                logger.error(f"- {file}")
        else:
            logger.info("所有文件处理完成！")

    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
