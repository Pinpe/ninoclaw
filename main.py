'''== 导入模块 =='''
from rich.panel import Panel
from lib import database
from lib import terminal
from lib import core
import rich.traceback
import rich.markdown
import rich.console
import textwrap
import curses
import time
import sys
import os


'''== 初始化 =='''
if os.name == 'posix':
    try:
        import gnureadline  # 用于修复在Linux下input()函数不好用的问题
    except ImportError:
        pass
elif os.name == 'nt':
    try:
        import pyreadline3  # Windows下的readline替代
    except ImportError:
        pass

rich.traceback.install(show_locals=True)         # 初始化rich样式的traceback
config         = database.load_data()['config']  # 预载配置文件，避免昂长调用
console        = rich.console.Console()          # 初始化rich的终端对象
user_cmd_input = None                            # 用户输入或命令输出，通常是给AI的，会经常改变
path           = config['home_path']             # 当前工作路径
diary_tip_num  = 0                               # 当此自增数字等于config['diary_tip_interval']时，提醒AI写日记
exec_state     = False                           # 是否为“执行状态”，在执行状态（正在执行任务）下按ctrl+c键会回到输入框，而不是退出程序


'''== 内部函数 =='''
def is_cd_command(cmd: str) -> bool:
    '''
    判断命令是否为cd命令。
    '''
    stripped = cmd.strip()
    return stripped == 'cd' or stripped.startswith('cd ') or stripped.startswith('cd\t')


'''== 内部函数 =='''
def cd_command(cmd):
    '''
    在命令交给命令执行器之前，如果发现输入的命令为cd，则可以执行这个特制的命令，更新path，不交给命令执行器。
    
    :param cmd: 要执行的命令
    '''
    global path, config
    # 去除掉cd、双引号和首尾空格，得到目标路径
    target = cmd.replace('cd', '').replace('\"', '').strip()
    # 处理 ~ 展开：如果目标路径以 ~ 开头，则替换为自定义的 HOME_DIR
    if target.startswith('~'):
        # 保留 ~ 后面的部分（如 /documents）
        target = config['home_path'] + target[1:]
    # 拼接当前路径并获取绝对路径
    new_path = os.path.abspath(os.path.join(path, target))
    # 检查新目录是否存在且为目录
    if os.path.isdir(new_path):
        path = new_path
        return f'目录已切换：{path}'
    else:
        return f'错误：目录不存在：{new_path}'

def run_sub_agent(task_desc: str) -> str:
    '''
    唤醒子助手处理任务。子助手拥有自己独立的临时上下文，不会污染主库。
    '''
    global path, config
    last_cmd = None
    sub_context = [f"[主控台] >> 请完成以下任务：{task_desc}"]  # 初始化子助手的临时上下文
    current_step = 0
    while current_step < config['sub_agent_max_steps']:
        current_step += 1
        # 动态加载 void.md 作为系统提示词
        sub_prompt = core.create_prompt(
            config['sub_agent_prompt_template_path'],
            sub_context
        )
        # 调用大模型 (使用子助手的临时上下文)
        ai_output = core.call_api(sub_prompt['context'], sub_prompt['system'])
        sub_context.append(f'[AI] >> {ai_output}')
        # 判断是否返回了最终结果
        if config['result_start_tag'] in ai_output:
            # 提取结果
            result_part = ai_output.split(config['result_start_tag'], 1)[1]
            result = result_part.split(config['result_end_tag'], 1)[0].strip()
            return str(result)
        # 判断是否需要执行命令
        elif config['cmd_start_tag'] in ai_output:
            cmd_part = ai_output.split(config['cmd_start_tag'], 1)[1]
            cmd = cmd_part.split(config['cmd_end_tag'], 1)[0].strip()
            console.print(
                ai_output.split(config['cmd_start_tag'], 1)[0] +
                f'（来自子助手，当前步数：{current_step}/{config['sub_agent_max_steps']}）'
            )
            terminal.dividing_line(style='yellow', characters='-')
            if cmd == last_cmd:
                cmd_output = "错误：你正在重复执行相同的命令，你可以尝试改变策略。"
            else:
                cmd_censor_result = terminal.confirm_modal(
                    f'请求执行命令：\n{cmd}',
                    yes = '通过',
                    no  = '驳回'
                ) if config['cmd_censor'] else True
                if cmd_censor_result == True:
                    last_cmd = cmd
                    # 复用原来的 cd 逻辑和命令执行逻辑
                    if is_cd_command(cmd):
                        cmd_output = cd_command(cmd)
                    else:
                        cmd_output = core.command_exec(cmd, path)
                else:
                    cmd_output = '用户驳回了这个命令，可能是这个命令有误或太危险，请检查'
            # 将执行结果追加到临时上下文中（主 Agent 看不到这些过程）
            sub_context.append(f"[返回结果] >> {cmd_output}")
        else:
            # 既没有命令也没有结果标签，可能是在思考或输出错误
            sub_context.append(f"AI输出格式错误：请务必使用标签执行命令或返回结果。")
    return "错误：子助手执行超时（超过最大思考步数），已强制熔断，你可以优化任务要求并重新尝试。"

def handle_command(ai_output: str) -> str:
    '''
    当发现AI的回复需要调用子助手时，在这里处理。

    :param ai_output: AI的输出。
    '''
    global path, user_cmd_input, config
    # 分离出聊天内容和任务内容
    ai_content, task_part = ai_output.split(config['task_start_tag'], 1)
    task_desc = task_part.split(config['task_end_tag'], 1)[0].strip()
    # 打印主 Agent 委派前的安抚话语（如果有的话）
    if ai_content.strip():
        console.print(rich.markdown.Markdown(ai_content))
        terminal.dividing_line()
        database.add_context(f'[{time.ctime()}][AI] >> {ai_output}')
    # 阻塞运行子助手，获取纯净的结果
    sub_result = run_sub_agent(task_desc)
    terminal.dividing_line()
    # 把子助手的结果作为“系统提示/输入”抛回给主循环，让 Pomi 根据结果总结回复
    return sub_result

def title_and_history() -> None:
    '''
    打印主程序的标题和上下文。
    '''
    global config
    console.clear();
    console.print(textwrap.dedent(f'''
        [cyan]⣿⣆⠱⣝⡵⣝⢅⠙⣿⢕⢕⢕⢕⢝⣥⢒⠅⣿⣿⣿⡿⣳⣌⠪⡪⣡⢑[/cyan]        [yellow]███╗   ██╗██╗███╗   ██╗ ██████╗  ██████╗██╗      █████╗ ██╗    ██╗[/yellow]
        [cyan]⣿⣿⣦⠹⣳⣳⣕⢅⠈⢗⢕⢕⢕⢕⢕⢈⢆⠟⠋⠉⠁⠉⠉⠁⠈⠼⢐[/cyan]        [yellow]████╗  ██║██║████╗  ██║██╔═══██╗██╔════╝██║     ██╔══██╗██║    ██║[/yellow]
        [cyan]⢰⣶⣶⣦⣝⢝⢕⢕⠅⡆⢕⢕⢕⢕⢕⣴⠏⣠⡶⠛⡉⡉⡛⢶⣦⡀⠐[/cyan]        [yellow]██╔██╗ ██║██║██╔██╗ ██║██║   ██║██║     ██║     ███████║██║ █╗ ██║[/yellow]
        [cyan]⡄⢻⢟⣿⣿⣷⣕⣕⣅⣿⣔⣕⣵⣵⣿⣿⢠⣿⢠⣮⡈⣌⠨⠅⠹⣷⡀[/cyan]        [yellow]██║╚██╗██║██║██║╚██╗██║██║   ██║██║     ██║     ██╔══██║██║███╗██║[/yellow]
        [cyan]⡵⠟⠈⢀⣀⣀⡀⠉⢿⣿⣿⣿⣿⣿⣿⣿⣼⣿⢈⡋⠴⢿⡟⣡⡇⣿⡇[/cyan]        [yellow]██║ ╚████║██║██║ ╚████║╚██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝[/yellow]
        [cyan]⠁⣠⣾⠟⡉⡉⡉⠻⣦⣻⣿⣿⣿⣿⣿⣿⣿⣿⣧⠸⣿⣦⣥⣿⡇⡿⣰[/cyan]        [yellow]╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ [/yellow]
        [cyan]⢰⣿⡏⣴⣌⠈⣌⠡⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣬⣉⣉⣁⣄⢖⢕[/cyan]
        [cyan]⢻⣿⡇⢙⠁⠴⢿⡟⣡⡆⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣵[/cyan]        [b green]版本：    3.7.1[/b green]
        [cyan]⣄⣻⣿⣌⠘⢿⣷⣥⣿⠇⣿⣿⣿⣿⣿⣿⠛⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿[/cyan]        [b red]作者：    Pinpe[/b red]
        [cyan]⢄⠻⣿⣟⠿⠦⠍⠉⣡⣾⣿⣿⣿⣿⣿⣿⢸⣿⣦⠙⣿⣿⣿⣿⣿⣿⣿[/cyan]        [b yellow]角色：    {config['prompt_template_name']}
        [cyan]⡑⣑⣈⣻⢗⢟⢞⢝⣻⣿⣿⣿⣿⣿⣿⣿⠸⣿⠿⠃⣿⣿⣿⣿⣿⣿⡿[/cyan]        [b blue]模型：    {config['model']}[/b blue]
        [cyan]⡵⡈⢟⢕⢕⢕⢕⣵⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣿⣿⣿⣿⣿⠿⠋⣀[/cyan]
    '''))
    # 如果发现有上下文（即上下文不为空），便把上下文打印出来
    context = database.load_data()['context']
    if context:
        for i in context:
            console.print(rich.markdown.Markdown(i))
            terminal.dividing_line()
        console.print('\n[black on blue] * [/black on blue][blue] 以上为历史消息[/blue]\n')
    console.print(Panel(
        '[white][yellow]summary[/yellow] 压缩上下文 [cyan]/[/cyan] [yellow]clear[/yellow] 清除上下文 [cyan]/[/cyan] [yellow]undo[/yellow] 删除上一条上下文 [cyan]/[/cyan] ' +
        '[yellow]command[/yellow] 执行Shell命令 [cyan]/[/cyan] [yellow]reload[/yellow] 重载程序 [cyan]/[/cyan] [yellow]exit[/yellow] 退出程序[/white]',
        title       = '输入',
        title_align = 'left',
        style       = 'cyan'
    ))
    console.print(Panel(
        '[white][yellow]Ctrl+C[/yellow] 中断任务或退出程序[/white]',
        title       = '按下',
        title_align = 'left',
        style       = 'blue'
    ))
    print()

def summary() -> None:
    '''
    执行用户输入的summary命令，摘要式压缩上下文。
    '''
    global config
    # 首先将上下文载入到变量里，方便修改
    context_list = database.load_data()['context']
    # 然后截取[0:config]条，生成摘要，并且插入到[0]中（最顶部）
    context_list.insert(0, '[摘要] >> ' + core.summary(
        database.load_data()['context'][:config['context_summary_input_len']],
        config['context_summary_len']
    ))
    # 然后删除，除了摘要的config条内容
    del context_list[1:config['context_summary_input_len']]
    database.format_json_dump(context_list, 'database/context.json')
    # 然后重载标题和上下文的显示
    title_and_history()
    console.print('\n[black on green] * [/black on green][green] 上下文压缩已完成[/green]\n')

def user_command() -> None:
    '''
    执行用户输入的command命令，手动执行shell命令。
    '''
    global exec_state
    cmd = console.input('[blue]$[/blue] ')
    # 如果命令是空白的，则回调到本函数，重新让用户输入
    if cmd == '':
        print()  # 这里加个换行，好看点
        return None  # 这里提前返回None，不知道为什么下面没有捕获
    database.add_context('[' + time.ctime() + '][' + path + '][用户自己执行命令] >> ' + cmd)
    # 处理cd命令，切换工作目录
    if is_cd_command(cmd):
        cmd_output = cd_command(cmd)
    else:
        cmd_output = core.command_exec(cmd, path)
    console.print(cmd_output)
    terminal.dividing_line()
    database.add_context('[' + time.ctime() + '][' + path + '][用户或返回结果] >> ' + cmd_output)

def clear_context():
    '''
    执行用户输入的clear命令，清空上下文。
    '''
    # 将文件覆写成空列表，这里直接对文件操作，免得让dump()添油加醋
    open('database/context.json', mode='w', encoding='UTF-8').write('[]')
    # 然后重载标题，打印个提示，和上面一样
    title_and_history()
    console.print('\n[black on green] * [/black on green][green] 上下文已清空[/green]\n')

def undo():
    '''
    执行用户输入的undo命令，删除上一条上下文。
    '''
    # 将上下文载入到变量里，然后删除变量最后一个元素，最后覆写到文件里
    context_list = database.load_data()['context']
    if context_list != []:
        del context_list[-1]
        database.format_json_dump(context_list, 'database/context.json')
    title_and_history()
    console.print('\n[black on green] * [/black on green][green] 已删除上一条上下文[/green]\n')

def user_input_box() -> str | None:
    '''
    用户的输入框，附带命令检查。
    '''
    user_input = console.input(
        f'[yellow][/yellow][black on yellow] {time.ctime()} [/black on yellow]'
        f'[yellow on blue][/yellow on blue]'
        f'[black on blue] {path} [/black on blue][blue][/blue]\n'
        f'[green]▶[/green] '
    )
    # 如果用户按了Ctrl+C的话就退出，否则traceback就糊脸了，下面的也是
    # 这个表定义了用户输入什么字段就执行什么（内部命令），只能用函数的引用和lambda函数
    cmd_table = {
        ''       : lambda: print(),
        'exit'   : lambda: sys.exit(0),
        'summary': summary,
        'clear'  : clear_context,
        'command': user_command,
        'undo'   : undo,
        'reload' : lambda: os.execv(sys.executable, [sys.executable] + sys.argv),
    }
    if user_input in cmd_table:  # 当发现用户输入是上表里面的值，就执行这个函数
        cmd_table[user_input]()  # 当然，虽然这个写法有点抽象，但的确能执行
    else:
        return user_input
    return None  # 返回None，会被此函数下面的一个判断（if userinput is None）截获，便不会运行之后的逻辑
                    # 只要不提前返回user_input就没事，有这个兜着


@terminal.command_proceessed('正在检查网络连通性...')
def connect_check():
    '''
    检查网络的连通性，并且在不可达时给出提示。
    '''
    global config
    if config['connect_check']:
        if not core.ping(config['base_url']):
            # 这里使用rich自己的print()而不是console的，因为会与加载动画造成未知冲突
            rich.print('\n[black on red] ! [/black on red][red] 网络不可达[/red]\n')

def diary_tip():
    '''
    如果diary_tip_num到达`config['diary_tip_interval]`时，则返回系统提示，否则返回空字符串
    '''
    global diary_tip_num, config
    # 然后检查当前diary_tip_num是否等于配置里的数
    if diary_tip_num == config['diary_tip_interval']:
        # 如果到了，就在给AI的输入加入系统提示，提醒随时检查日记，同时把这个数归零
        diary_tip_num = 0
        return '（系统提示：在完成一个任务或话题后就要检查修订日记）'
    # 如果没有，就不用加提醒，但默默地把这个数+1，直到等于配置里的数为止
    else:
        diary_tip_num += 1
        return ''


'''== 主程序 =='''
if __name__ == '__main__':
    # 首先打印大标题和上下文
    title_and_history()
    # 检查网络连通性
    connect_check()
    # 如果发现没有今天的日记，就创建一个
    database.create_diary()
    # 开始大循环
    while True:
        try:
            # 当没有命令输出时，让用户输入，否则则代表有命令返回
            if user_cmd_input is None:
                exec_state = False # 在主输入框等待时，处于非执行状态
                user_cmd_input = user_input_box()
                if user_cmd_input is None: continue
            exec_state = True  # 拿到输入并开始请求AI或执行任务，进入执行状态
            # 执行diary_tip（日记检查）
            diary_tip_str = diary_tip()
            # 将用户的输入添加到上下文
            database.add_context('[' + time.ctime() + '][' + path + '][用户输入或返回结果] >> ' + user_cmd_input + diary_tip_str)
            # 创建提示词输入，然后传递给AI
            prompt = core.create_prompt(
                config['prompt_template_path'],
                database.load_data()['context']
            )
            ai_output = core.call_api(prompt['context'], prompt['system'])
            # 如果发现AI需要执行（发现包含成对标签）
            if config['task_start_tag'] in ai_output \
            and config['task_end_tag'] in ai_output:
                user_cmd_input = handle_command(ai_output)
            # 如果不是的话
            else:
                console.print(rich.markdown.Markdown(ai_output))
                terminal.dividing_line()
                terminal.send_notify(ai_output, '收到了新消息！')  # 完成任务或回复时显示通知
                database.add_context('[' + time.ctime() + '][AI] >> ' + ai_output)
                # 重置用户的输入，让下一次循环可以被输入框判断并接住
                user_cmd_input = None
        except KeyboardInterrupt:
            if exec_state == True:
                print()  # 加个空格，美化
                user_cmd_input = None
                exec_state = False
                continue
            else:
                sys.exit(0)