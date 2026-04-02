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
def call_api(prompt: str) -> str:
    '''
    直接将**原始**的提示词发送给AI，是与AI交互的直接接口。

    :param prompt: 给AI的**原始**提示词。
    '''
    global api_retry_num
    while True:
        try:
            data = database.load_data()
            client = OpenAI(
                api_key  = data['env']['ai_api_key'],
                base_url = data['config']['base_url'],
                timeout  = data['config']['api_time_out']
            )
            response = client.chat.completions.create(
                model    = data['config']['model'],
                stream   = False,
                messages = [{
                    "role":    "user",
                    "content": prompt
                }]
            )
            api_retry_num = 0
            return response.choices[0].message.content
        except Exception as err:
            if api_retry_num < database.load_data()['config']['api_retry_num']:
                time.sleep(database.load_data()['config']['api_retry_sleep'])
                api_retry_num += 1
            else:
                raise err


def create_prompt() -> str:
    '''
    根据各种数据，整合和创建给AI的提示词。
    '''
    data = database.load_data()
    config = data['config']

    context_str = ''
    skill_str = ''
    # 格式化上下文列表，每行一条上下文
    for i in data['context']:
        context_str += (i + '\n')
    # 格式化skill列表，格式同上
    for i in config['skill']:
        skill_str += (i + '\n')

    # 读取提示词模板文件
    with open(config['prompt_template_path'], encoding='UTF-8') as f:
        template = f.read()

    # 读取记忆文件
    memory_path = os.path.join(config['home_path'], 'MEMORY.md')
    with open(memory_path, encoding='UTF-8') as f:
        memory_content = f.read()

    # 读取今日日记
    diary_path = os.path.join(config['home_path'], 'diary', str(datetime.date.today()) + '.md')
    with open(diary_path, encoding='UTF-8') as f:
        diary_content = f.read()

    # 使用 {{placeholder}} 占位符替换，安全且可读
    replacements = {
        '{{home_path}}': config['home_path'],
        '{{cmd_start_tag}}': config['cmd_start_tag'],
        '{{cmd_end_tag}}': config['cmd_end_tag'],
        '{{today}}': str(datetime.date.today()),
        '{{memory_content}}': memory_content,
        '{{diary_content}}': diary_content,
        '{{skill_str}}': skill_str,
        '{{context_str}}': context_str,
    }
    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    return prompt


def _get_shell_info():
    '''
    根据操作系统返回合适的 shell 和配置信息。
    '''
    config = database.load_data()['config']
    shell = config.get('shell')
    shell_config = config.get('shell_config')

    if shell:
        return shell, shell_config

    # 自动检测
    if os.name == 'nt':
        # Windows: 使用 cmd.exe
        return os.environ.get('COMSPEC', 'cmd.exe'), None
    else:
        # Linux/macOS: 使用用户默认 shell
        return os.environ.get('SHELL', '/bin/bash'), shell_config


@terminal.command_proceessed('正在执行命令...')
def command_exec(cmd: str, path: str) -> str:
    '''
    执行shell命令。

    :param cmd: 需要执行的命令。
    :param path: 当前所在的目录。
    '''
    config = database.load_data()['config']
    time.sleep(config['cmd_sleep'])
    shell_exe, shell_config = _get_shell_info()

    try:
        if os.name == 'nt':
            # Windows: 直接通过 cmd.exe 执行
            output = subprocess.run(
                args           = cmd,
                capture_output = True,
                text           = True,
                cwd            = path,
                timeout        = config['cmd_time_out'],
                shell          = True
            )
        else:
            # Linux/macOS: 加载 shell 配置后执行
            source_cmd = ':' if shell_config is None else 'source ' + shell_config
            output = subprocess.run(
                args           = [source_cmd + ' ; ' + cmd],
                capture_output = True,
                text           = True,
                cwd            = path,
                timeout        = config['cmd_time_out'],
                shell          = True,
                executable     = shell_exe
            )

        if output.stderr:
            return output.stderr
        elif not output.stdout:
            return '（无文本输出）'
        else:
            return output.stdout
    except subprocess.TimeoutExpired:
        return '执行命令超时：' + str(config['cmd_time_out']) + '秒上限'
    except Exception as err:
        return '由于某些因素，命令执行器本身出现了错误：' + str(err)


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
