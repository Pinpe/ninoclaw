'''
NinoClaw的核心API，集成了必要且实用的工具。
'''


from openai import OpenAI
from lib    import database
from lib    import terminal
import subprocess
import textwrap
import datetime
import time


@terminal.command_proceessed('pomi正在思考中...')
def call_api(prompt: str) -> str:
    '''
    直接将**原始**的提示词发送给AI，是与AI交互的直接接口。

    :param prompt: 给AI的**原始**提示词。
    '''
    try:
        client = OpenAI(
            api_key  = database.load_data()['env']['ai_api_key'],
            base_url = database.load_data()['config']['base_url']
        )
        response = client.chat.completions.create(
            model    = database.load_data()['config']['model'],
            stream   = False,
            messages = [{
                "role":    "user",
                "content": prompt
            }]
        )
        return str(response.choices[0].message.content)
    except Exception as err:
        return str(err)  # 当API调用出现问题，会直接返回错误信息，请注意捕获
"""
def call_api(prompt: str) -> str:
    print(prompt)
    return input('[debug AI] >> ')
"""


def create_prompt() -> str:
    '''
    根据各种数据，整合和创建给AI的提示词。
    '''
    context_str = ''
    skill_str = ''
    # 格式化上下文列表，每行一条上下文
    for i in database.load_data()['context']:
        context_str += (i + '\n')
    # 格式化skill列表，格式同上
    for i in database.load_data()['config']['skill']:
        skill_str += (i + '\n')
    # 返回提示词
    # 先读取提示词模板文件（open），然后格式化文件内容为多行字符串（"""{}"""），最后填充模板（eval）
    return eval(f'f"""{open('prompt_template.txt', encoding='UTF-8').read()}"""')


@terminal.command_proceessed('pomi正在执行命令...')
def command_exec(input: str, path: str) -> str:
    '''
    执行shell命令。

    :param input: 需要执行的命令。
    :param path: 当前所在的目录。
    '''
    time.sleep(5)  # 这里加个阻塞，调用太快可能会被排队
    try:
        output =  subprocess.run(
            args           = [f'source {database.load_data()['config']['shell_config']} ; {input}'],
            capture_output = True,
            text           = True,
            cwd            = path,
            timeout        = database.load_data()['config']['cmd_time_out'],  # 超时会抛出TimeoutExpired，下面也有捕获
            shell          = True,  # 真正的使用shell是executable，这个就不要动了
            executable     = database.load_data()['config']['shell']
        )
        if output.stderr:  # shell使用stdout输出，却使用stderr报错，很奇怪，这是报错的分支
            return output.stderr
        elif not output.stdout:  # 没有报错也没有输出的情况下...
            return '（无文本输出）'
        else:
            return output.stdout
    except subprocess.TimeoutExpired:
        return f'执行命令超时：{database.load_data()['config']['cmd_time_out']}秒上限'
    except Exception as err:
        return f'由于某些因素，命令执行器本身出现了错误：{err}'  # 这里也直接返回了错误信息，请注意捕获


def summary(content, len: int) -> str:
    '''
    总结任何文本内容。

    :param content: 需要总结的内容。
    :param len: 总结后的长度（字），不保证完全对上。
    '''
    return call_api(f'总结以下内容，不少于{len}字：\n{content}')