'''
NinoClaw的核心API，集成了必要且实用的工具。
'''


from openai import OpenAI
from lib    import database
from lib    import terminal
import subprocess
import datetime
import requests
import time
import os


api_retry_num = 0


@terminal.command_proceessed('正在思考中...')
def call_api(user: str, system: str = '') -> str:
    '''
    直接将**原始**的提示词发送给AI，是与AI交互的直接接口。

    :param user: 给AI的**原始**提示词。
    :param system: 给AI的**原始**系统提示词，可省略。
    '''
    global api_retry_num
    while True:
        try:
            client = OpenAI(
                api_key  = database.load_data()['env']['ai_api_key'],
                base_url = database.load_data()['config']['base_url'],
                timeout  = database.load_data()['config']['api_time_out']
            )
            response = client.chat.completions.create(
                model    = database.load_data()['config']['model'],
                stream   = False,
                messages = [
                    {'role': 'assistant', 'content': system},
                    {'role': 'user',      'content': user}
                ]
            )
            api_retry_num = 0
            return response.choices[0].message.content
        except Exception as err:
            if api_retry_num < database.load_data()['config']['api_retry_num']:
                time.sleep(database.load_data()['config']['api_retry_sleep'])
                api_retry_num += 1
            else:
                raise err
"""
def call_api(user: str, system: str = '') -> str:
    '''
    这是用于debug的假接口，用法和上面一样，但不会提交到真api，而是stdio。\n
    取消注释即可使用。
    '''
    print(f'{'='*80}\n' + system + f'\n{'-'*80}\n' + user)
    return input('[debug AI] >> ')
"""


def create_prompt(template_path: str, context: list) -> str:
    '''
    根据各种数据，整合和创建给主Agent的提示词。

    :param template_path: 提示词模板文件。
    :param context: 上下文列表。
    '''
    context_str = ''
    skill_str = ''
    # 格式化上下文列表，每行一条上下文
    for i in context:
        context_str += (i + '\n')
    # 格式化skill列表，格式同上
    for i in database.load_data()['config']['skill']:
        skill_str += (i + '\n')
    # 返回提示词
    # 先读取提示词模板文件（open），然后格式化文件内容为多行字符串（"""{}"""），最后填充模板（eval）
    return {
        'context': context_str,
        'system':  eval(
                    f'f"""{open(
                        template_path,
                        encoding='UTF-8'
                    ).read()}"""')
    }


@terminal.command_proceessed('正在执行命令...')
def command_exec(input: str, path: str) -> str:
    '''
    执行shell命令。

    :param input: 需要执行的命令。
    :param path: 当前所在的目录。
    '''
    time.sleep(database.load_data()['config']['cmd_sleep'])  # 这里加个阻塞，调用太快可能会被排队
    shell_config = database.load_data()['config']['shell_config']
    try:
        output =  subprocess.run(
            # 当配置为null时，返回bash空占位符（:），否则就返回source {config['shell_config']}
            args           = [f'{':' if shell_config == None else f'source {shell_config}'} ; {input}'],
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


def summary(content: str, max_len: int) -> str:
    '''
    总结任何文本内容。

    :param content: 需要总结的内容。
    :param max_len: 总结后的长度（字），不保证完全对上。
    '''
    return call_api('总结以下内容，需要保留所有要点和信息，不少于' + str(max_len) + '字：\n' + str(content))


def ping(url: str) -> bool:
    '''
    检查某个远程URL的连通性，返回布尔值。
    '''
    try:
        requests.get(
            url,
            timeout=database.load_data()['config']['connect_check_time_out']
        ).status_code
        return True
    except Exception:
        return False
