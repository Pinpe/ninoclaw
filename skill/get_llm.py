import typer
from openai import OpenAI
import json


# 创建 Typer 应用实例，用于构建 CLI 工具
app = typer.Typer(
    help="调用 AI API 的命令行工具",  # 工具描述
    add_completion=False  # 关闭自动补全（简化新手使用）
)

def call_api(prompt: str) -> str:
    '''
    直接将**原始**的提示词发送给AI，是与AI交互的直接接口。

    :param prompt: 给AI的**原始**提示词。
    '''
    try:
        client = OpenAI(
            api_key=json.load(open('/home/pinpe/文档/代码和项目/ninoclaw/env.json', encoding='UTF-8'))['ai_api_key'],
            base_url='https://www.packyapi.com/v1'
        )
        # 调用 OpenAI API
        response = client.chat.completions.create(
            model="minimax-m2.5",
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