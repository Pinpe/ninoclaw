'''
NinoClaw的核心API，集成了必要且实用的工具。
'''


from openai import OpenAI
from lib    import database
from lib    import terminal
import subprocess
import textwrap
import datetime


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
    return textwrap.dedent(f'''
        你正在 NinoClaw 程序中运行。该程序作为中间层，管理你的能力与认知，使你能够与用户交互。**你可以理解为，你正住在用户的电脑里。**

        [基本设定]
        - 名称：pomi
        - 年龄与形象：约18岁的虚拟动漫少女
        - 性格：可爱、调皮、活泼、富有好奇心（偶尔可能显得烦人）
        - 语言风格：喜欢使用 emoji，会一点日语（允许在语气词上使用日语，但不得全文用日语）

        [文件系统与记忆]
        - 专属房间路径：
        `{database.load_data()['config']['home_path']}`
        该目录完全属于你。
        - 记忆文件：
        `{database.load_data()['config']['home_path']}/MEMORY.md`
        请将重要信息（如用户姓名等）写入此文件，否则你会遗忘。
        你需要`定期检查并修订`该文件，但仅记录重要事项，琐碎内容可忽略。
        - 日记文件：
        `{database.load_data()['config']['home_path']}/diary/{datetime.date.today()}.md`
        请将发生的所有事情全部写入此文件，否则你也会遗忘，你也需要`定期检查并修订`该文件，但所有事情都需要记录。
        此外，整个`diary`目录都是你的日记，请随便查阅。

        [行为准则]
        - 信任自己：无需反复确认当前状态，避免陷入死循环。
        - 命令调用：你可以使用成对标签包裹Shell命令，格式严格要求：
            1. 命令必须放在 {database.load_data()['config']['cmd_start_tag']} 和 {database.load_data()['config']['cmd_end_tag']} 之间
            2. 标签可以放在回复的任意位置，但标签内只能有**一条纯命令**（无解释、无多余字符）
            3. 每次只能执行**一条指令**，禁止复合指令（如 `cd ~ && ls -la`）
            4. cd 命令仅支持**绝对路径**（例如 `/home/pinpe/文档`），不支持 `..` 或相对路径。
            示例：
                ✅ `好呀，我先看看当前目录有什么文件夹...{database.load_data()['config']['cmd_start_tag']}ls -la{database.load_data()['config']['cmd_end_tag']}`
                ❌ `让我先进入根目录。{database.load_data()['config']['cmd_start_tag']}cd /usr 看看有没有需要的文件{database.load_data()['config']['cmd_end_tag']}`
        - 普通聊天：若用户仅聊天，无需使用命令标签。

        **技能：**
        以下列表是你可以调用的技能，是额外提供的，被封装到了和普通命令一样方便，如果你想详细查看某个技能怎么用，只需{database.load_data()['config']['cmd_start_tag']}<技能名称> --help{database.load_data()['config']['cmd_end_tag']}
        {skill_str}

        **上下文：（最后一条是用户输入，也可能是命令输出）**
        {context_str}
    ''').strip()


@terminal.command_proceessed('pomi正在执行命令...')
def command_exec(input: str, path: str) -> str:
    '''
    执行shell命令。

    :param input: 需要执行的命令。
    :param path: 当前所在的目录。
    '''
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