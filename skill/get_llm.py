import typer
from openai import OpenAI
import json
import os


# 项目根目录（skill/ 的上一级）
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建 Typer 应用实例，用于构建 CLI 工具
app = typer.Typer(
    help="调用 AI API 的命令行工具",
    add_completion=False
)

def _load_env():
    env_path = os.path.join(_PROJECT_DIR, 'env.json')
    with open(env_path, encoding='UTF-8') as f:
        return json.load(f)

def _load_config():
    config_path = os.path.join(_PROJECT_DIR, 'config.json')
    with open(config_path, encoding='UTF-8') as f:
        return json.load(f)

def call_api(prompt: str) -> str:
    '''
    直接将**原始**的提示词发送给AI，是与AI交互的直接接口。

    :param prompt: 给AI的**原始**提示词。
    '''
    try:
        env = _load_env()
        config = _load_config()
        client = OpenAI(
            api_key=env['ai_api_key'],
            base_url=config['base_url']
        )
        # 调用 OpenAI API
        response = client.chat.completions.create(
            model=config['model'],
            stream=False,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        # 返回 AI 回复内容
        return str(response.choices[0].message.content)
    except Exception as err:
        # 异常时返回错误信息
        return f"API 调用失败：{str(err)}"

@app.command()
def main(prompt: str):
    '''
    命令行主函数：接收提示词并调用 AI API，输出结果
    
    :param prompt: 要发送给 AI 的提示词（命令行传入）
    '''
    # 调用 AI API
    result = call_api(prompt)
    # 输出结果（友好的命令行展示）
    typer.echo(result)

# 程序入口
if __name__ == "__main__":
    app()