import typer
import base64
import os
import textwrap
from openai import OpenAI
from openai import APIError, AuthenticationError, APIConnectionError
import json

# 初始化 Typer 应用
app = typer.Typer(help="图片识别AI命令行工具，调用通义千问VL模型分析图片内容")

def image_to_base64(image_path: str) -> str:
    """
    将本地图片文件转换为base64编码字符串
    
    :param image_path: 本地图片文件的路径
    :return: 图片的base64编码字符串
    """
    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在：{image_path}")
    
    # 检查文件是否为有效图片（简单后缀校验）
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    if not image_path.lower().endswith(valid_extensions):
        raise ValueError(f"不支持的图片格式，仅支持：{valid_extensions}")
    
    # 读取并编码图片
    with open(image_path, "rb") as image_file:
        # 编码为base64并转换为字符串（去除b''前缀）
        base64_encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return base64_encoded

def get_vision_ai(img_base: str, prompt: str) -> str:
    '''
    将提示词和图片发给图片识别AI，获取图片识别结果
    
    :param img_base: 图片的base64编码
    :param prompt: 给AI的提示词
    :return: AI返回的识别结果
    '''
    # 从环境变量获取API Key（推荐方式，避免硬编码）
    api_key = api_key=json.load(open('/home/pinpe/文档/代码和项目/ninoclaw/env.json', encoding='UTF-8'))['vision_api_key']
    if not api_key:
        raise ValueError(
            "未找到API Key"
        )
    
    # 初始化OpenAI客户端（兼容通义千问）
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    try:
        completion = client.chat.completions.create(
            model="qwen3-vl-8b-instruct",
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

def create_vision_prompt() -> str:
    '''
    创建给图像识别AI的提示词
    '''
    return textwrap.dedent('''
        请严格遵循以下步骤和格式，对提供的图片进行详细描述，不要输出任何多余内容，描述成一段落，禁止使用任何小标题分割，100字以内：

        第一步：整体内容概括
        用一句话概括图片的核心主题或场景（例如：这是一张包含产品说明的电商海报）。

        第二步：详细视觉元素描述
        主体与场景： 描述图片中的主要人物、物体、背景环境、布局和颜色基调。
        关键文本信息（逐项列出）：
        位置与形式： 明确指出文本出现在图片的哪个区域（如顶部标题、底部小字、产品标签等），以及其形式（印刷体、手写体、艺术字、屏幕截图等）。
        内容转录： 将图片中的所有文字一字不差、原样转录（包括拼写错误或特殊符号）。即使文字不清晰，也请尽力辨识并说明。
        字体与风格： 描述文字的视觉风格（如加粗、斜体、字体大小、颜色）及其可能传达的情绪或重点。

        第三步：文本与视觉的关联分析
        解释图片中的文字如何与视觉元素相互作用。例如：文本是否为视觉元素的标签、说明、标题或补充信息？它是否在引导观看者的注意力？

        第四步：综合摘要与目的推断
        基于以上所有信息，总结这张图片可能的目的、受众和传达的核心信息（例如：这是一张宣传新科技产品的广告，旨在通过突出性能参数吸引消费者）。
    ''').strip()  # 去除首尾空白符

@app.command()
def analyze_image(image_path: str):
    """
    分析指定路径的图片内容
    
    :param image_path: 本地图片文件的路径（支持绝对路径/相对路径）
    """
    try:
        
        # 1. 转换图片为base64编码
        img_base64 = image_to_base64(image_path)
        
        # 2. 创建提示词
        prompt = create_vision_prompt()
        
        # 3. 调用AI分析图片
        result = get_vision_ai(img_base64, prompt)
        
        # 4. 输出结果
        typer.echo(result)
        
    except Exception as e:
        typer.secho(f"\n❌ 处理失败：{str(e)}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()