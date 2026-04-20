#!/usr/bin/env python3
import typer
import base64
import os
import json
from openai import OpenAI
from openai import APIError, AuthenticationError, APIConnectionError

# 项目根目录
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 初始化 Typer 应用
app = typer.Typer(help="OCR文字识别工具，调用通义千问VL模型识别图片中的文字")

def image_to_base64(image_path: str) -> str:
    """
    将本地图片文件转换为base64编码字符串
    
    :param image_path: 本地图片文件的路径
    :return: 图片的base64编码字符串
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在：{image_path}")
    
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    if not image_path.lower().endswith(valid_extensions):
        raise ValueError(f"不支持的图片格式，仅支持：{valid_extensions}")
    
    with open(image_path, "rb") as image_file:
        base64_encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return base64_encoded

def get_ocr_result(img_base: str, prompt: str) -> str:
    """
    将图片发给OCR AI，获取文字识别结果
    
    :param img_base: 图片的base64编码
    :param prompt: 给AI的提示词
    :return: AI返回的识别结果
    """
    env_path = os.path.join(_PROJECT_DIR, 'env.json')
    with open(env_path, encoding='UTF-8') as f:
        api_key = json.load(f)['vision_api_key']
    if not api_key:
        raise ValueError("未找到API Key")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://www.packyapi.com/v1",
    )
    
    try:
        completion = client.chat.completions.create(
            model="qwen3-vl-flash",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f'data:image/png;base64,{img_base}'
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        return completion.choices[0].message.content
    except AuthenticationError:
        raise Exception("API Key无效或认证失败，请检查你的API Key")
    except APIConnectionError:
        raise Exception("网络连接失败，无法连接到AI服务")
    except APIError as e:
        raise Exception(f"AI服务调用失败：{e.message}")
    except Exception as e:
        raise Exception(f"未知错误：{str(e)}")

def create_ocr_prompt() -> str:
    """
    创建给OCR AI的提示词 - 专门识别图片中的所有文字
    """
    return """请仔细识别图片中的所有文字，包括印刷体、手写体、屏幕截图等。

要求：
1. 逐行转录所有文字，一字不差
2. 如果有换行，保持原有换行结构
3. 对于不清晰的文字，尽量辨认并标注（用括号表示不确定）
4. 如果图片中没有文字，请输出"图片中未识别到文字"
5. 只输出文字内容，不要输出任何描述或分析"""

@app.command()
def recognize(
    image_path: str = typer.Argument(..., help="要识别文字的图片路径")
):
    """
    识别指定图片中的文字
    
    :param image_path: 本地图片文件的路径（支持绝对路径/相对路径）
    """
    try:
        # 1. 转换图片为base64编码
        img_base64 = image_to_base64(image_path)
        
        # 2. 创建OCR提示词
        prompt = create_ocr_prompt()
        
        # 3. 调用AI识别文字
        result = get_ocr_result(img_base64, prompt)
        
        # 4. 输出结果
        typer.echo(result)
        
    except Exception as e:
        typer.secho(f"处理失败：{str(e)}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
