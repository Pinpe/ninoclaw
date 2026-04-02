'''== 导入模块 =='''
from lib import database
from lib import terminal
from lib import core
import rich.traceback
import rich.markdown
import rich.console
import textwrap
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

rich.traceback.install(show_locals=True)                      # 初始化rich样式的traceback
console        = rich.console.Console()                       # 初始化rich的终端对象
user_cmd_input = None                                         # 用户输入或命令输出，通常是给AI的，会经常改变
path           = database.load_data()['config']['home_path']  # 当前工作路径
last_cmd       = None                                         # 上一条AI执行的命令，用于和当前命令比对，防止死循环
diary_tip_num  = 0                                            # 当此自增数字等于config['diary_tip_interval']时，提醒AI写日记


'''== 内部函数 =='''
def _is_cd_command(cmd: str) -> bool:
    '''
    判断命令是否为cd命令。
    '''
    stripped = cmd.strip()
    return stripped == 'cd' or stripped.startswith('cd ') or stripped.startswith('cd\t')


def cd_command(cmd):
    '''
    在命令交给命令执行器之前，如果发现输入的命令为cd，则可以执行这个特制的命令，更新path，不交给命令执行器。

    :param cmd: 要执行的命令
    '''
    global path
    # 去除掉cd、双引号和首尾空格，得到目标路径
    target = cmd.strip()[2:].replace('"', '').strip()
    # 处理 ~ 展开：如果目标路径以 ~ 开头，则替换为自定义的 HOME_DIR
    if target.startswith('~'):
        home = database.load_data()['config']['home_path']
        target = home + target[1:]
    # 拼接当前路径并获取绝对路径
    new_path = os.path.abspath(os.path.join(path, target))
    # 检查新目录是否存在且为目录
    if os.path.isdir(new_path):
        path = new_path
        return '目录已切换：' + path
    else:
        return '错误：目录不存在：' + new_path


def handle_command(ai_output: str) -> str:
    '''
    当发现AI的回复需要执行命令时，在这里处理。

    :param ai_output: AI的输出。
    '''
    global path, user_cmd_input, last_cmd
    data = database.load_data()
    cmd_start_tag = data['config']['cmd_start_tag']
    cmd_end_tag = data['config']['cmd_end_tag']

    # 分割开始标签，分离AI回复内容和命令部分
    ai_content, cmd_part = ai_output.split(cmd_start_tag, 1)
    # 分割结束标签，只保留标签内的命令
    cmd = cmd_part.split(cmd_end_tag, 1)[0].strip()
    # 打印AI回复并记录上下文
    console.print(rich.markdown.Markdown(ai_content))
    terminal.dividing_line()
    database.add_context(
        '[' + time.ctime() + '][AI] >> ' + ai_content
        + cmd_start_tag + cmd + cmd_end_tag
    )
    # 判断AI的命令是否与上一条命令相等，防止死循环
    if cmd == last_cmd:
        return '错误：不能执行与上一条相同的命令，如果需要执行，你可以给命令加入多余参数或注释。此机制是为了防止你陷入无限循环。'
    # 校验通过后，更新last命令
    last_cmd = cmd
    # 处理cd命令，切换工作目录
    if _is_cd_command(cmd):
        return cd_command(cmd)
    # 执行命令，返回执行结果
    return core.command_exec(cmd, path)

def title_and_history() -> None:
    '''
    打印主程序的标题和上下文。
    '''
    console.clear()
    console.print(textwrap.dedent('''
        [cyan]⣿⣆⠱⣝⡵⣝⢅⠙⣿⢕⢕⢕⢕⢝⣥⢒⠅⣿⣿⣿⡿⣳⣌⠪⡪⣡⢑[/cyan]        [yellow]███╗   ██╗██╗███╗   ██╗ ██████╗  ██████╗██╗      █████╗ ██╗    ██╗[/yellow]
        [cyan]⣿⣿⣦⠹⣳⣳⣕⢅⠈⢗⢕⢕⢕⢕⢕⢈⢆⠟⠋⠉⠁⠉⠉⠁⠈⠼⢐[/cyan]        [yellow]████╗  ██║██║████╗  ██║██╔═══██╗██╔════╝██║     ██╔══██╗██║    ██║[/yellow]
        [cyan]⢰⣶⣶⣦⣝⢝⢕⢕⠅⡆⢕⢕⢕⢕⢕⣴⠏⣠⡶⠛⡉⡉⡛⢶⣦⡀⠐[/cyan]        [yellow]██╔██╗ ██║██║██╔██╗ ██║██║   ██║██║     ██║     ███████║██║ █╗ ██║[/yellow]
        [cyan]⡄⢻⢟⣿⣿⣷⣕⣕⣅⣿⣔⣕⣵⣵⣿⣿⢠⣿⢠⣮⡈⣌⠨⠅⠹⣷⡀[/cyan]        [yellow]██║╚██╗██║██║██║╚██╗██║██║   ██║██║     ██║     ██╔══██║██║███╗██║[/yellow]
        [cyan]⡵⠟⠈⢀⣀⣀⡀⠉⢿⣿⣿⣿⣿⣿⣿⣿⣼⣿⢈⡋⠴⢿⡟⣡⡇⣿⡇[/cyan]        [yellow]██║ ╚████║██║██║ ╚████║╚██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝[/yellow]
        [cyan]⠁⣠⣾⠟⡉⡉⡉⠻⣦⣻⣿⣿⣿⣿⣿⣿⣿⣿⣧⠸⣿⣦⣥⣿⡇⡿⣰[/cyan]        [yellow]╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ [/yellow]
        [cyan]⢰⣿⡏⣴⣌⠈⣌⠡⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣬⣉⣉⣁⣄⢖⢕[/cyan]
        [cyan]⢻⣿⡇⢙⠁⠴⢿⡟⣡⡆⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣵[/cyan]                        [b green]版本：3.7.0[/b green]      [b red]作者：Pinpe[/b red]
        [cyan]⣄⣻⣿⣌⠘⢿⣷⣥⣿⠇⣿⣿⣿⣿⣿⣿⠛⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿[/cyan]
        [cyan]⢄⠻⣿⣟⠿⠦⠍⠉⣡⣾⣿⣿⣿⣿⣿⣿⢸⣿⣦⠙⣿⣿⣿⣿⣿⣿⣿[/cyan]    输入：    [yellow]summary[/yellow] 压缩上下文       [yellow]clear[/yellow] 清除上下文    [yellow]undo[/yellow] 删除上一条上下文
        [cyan]⡑⣑⣈⣻⢗⢟⢞⢝⣻⣿⣿⣿⣿⣿⣿⣿⠸⣿⠿⠃⣿⣿⣿⣿⣿⣿⡿[/cyan]              [yellow]command[/yellow] 执行Shell命令    [yellow]exit[/yellow]  退出
        [cyan]⡵⡈⢟⢕⢕⢕⢕⣵⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣿⣿⣿⣿⣿⠿⠋⣀[/cyan]
    '''))
    # 如果发现有上下文（即上下文不为空），便把上下文打印出来
    context = database.load_data()['context']
    if context:
        for i in context:
            console.print(rich.markdown.Markdown(i))
            terminal.dividing_line()
        console.print('\n[black on blue] 以上为历史消息 [/black on blue]\n')

def summary() -> None:
    '''
    执行用户输入的summary命令，摘要式压缩上下文。
    '''
    data = database.load_data()
    context_list = data['context']
    summary_input_len = data['config']['context_summary_input_len']
    summary_len = data['config']['context_summary_len']
    # 截取前N条生成摘要，插入到最顶部
    context_list.insert(0, '[摘要] >> ' + core.summary(
        context_list[:summary_input_len],
        summary_len
    ))
    # 删除已被摘要的原始条目
    del context_list[1:summary_input_len]
    database.format_json_dump(context_list, 'database/context.json')
    title_and_history()
    console.print('\n[black on green] 上下文压缩已完成 [/black on green]\n')

def user_command() -> None:
    '''
    执行用户输入的command命令，手动执行shell命令。
    '''
    try:
        cmd = console.input('[blue]$[/blue] ')
    except KeyboardInterrupt:
        sys.exit(0)
    if cmd == '':
        print()
        return None
    database.add_context('[' + time.ctime() + '][' + path + '][用户自己执行命令] >> ' + cmd)
    # 处理cd命令，切换工作目录
    if _is_cd_command(cmd):
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
    database.format_json_dump([], 'database/context.json')
    title_and_history()
    console.print('\n[black on green] 上下文已清空 [/black on green]\n')

def undo():
    '''
    执行用户输入的undo命令，删除上一条上下文。
    '''
    context_list = database.load_data()['context']
    if context_list:
        del context_list[-1]
        database.format_json_dump(context_list, 'database/context.json')
    title_and_history()
    console.print('\n[black on green] 已删除上一条上下文 [/black on green]\n')

def user_input_box() -> str | None:
    '''
    用户的输入框，附带命令检查。
    '''
    try:
        user_input = console.input(
            '[black on yellow] ' + time.ctime() + ' [/black on yellow]'
            '[yellow on blue][/yellow on blue]'
            '[black on blue] ' + path + ' [/black on blue][blue][/blue]\n'
            '[green]▶[/green] '
        )
    except KeyboardInterrupt:
        sys.exit(0)
    cmd_table = {
        ''       : lambda: print(),
        'exit'   : lambda: sys.exit(0),
        'summary': summary,
        'clear'  : clear_context,
        'command': user_command,
        'undo'   : undo
    }
    if user_input in cmd_table:
        cmd_table[user_input]()
    else:
        return user_input
    return None


@terminal.command_proceessed('正在检查网络连通性...')
def connect_check():
    '''
    检查网络的连通性，并且在不可达时给出提示。
    '''
    config = database.load_data()['config']
    if config['connect_check']:
        if not core.ping(config['base_url']):
            rich.print('\n[black on red] 网络不可达 [/black on red]\n')

def diary_tip():
    '''
    如果diary_tip_num到达config['diary_tip_interval']时，则返回系统提示，否则返回空字符串
    '''
    global diary_tip_num
    if diary_tip_num == database.load_data()['config']['diary_tip_interval']:
        diary_tip_num = 0
        return '（系统提示：在完成一个任务或话题后就要检查修订日记）'
    else:
        diary_tip_num += 1
        return ''


'''== 主程序 =='''
if __name__ == '__main__':
    # 切换工作目录到项目根目录，确保相对路径正确
    os.chdir(database.PROJECT_DIR)
    # 首先打印大标题和上下文
    title_and_history()
    # 检查网络连通性
    connect_check()
    # 如果发现没有今天的日记，就创建一个
    database.create_diary()
    # 开始大循环
    while True:
        # 当没有命令输出时，让用户输入，否则则代表有命令返回
        if user_cmd_input is None:
            user_cmd_input = user_input_box()
            if user_cmd_input is None: continue
        # 执行diary_tip（日记检查）
        diary_tip_str = diary_tip()
        # 将用户的输入添加到上下文
        database.add_context('[' + time.ctime() + '][' + path + '][用户或返回结果] >> ' + user_cmd_input + diary_tip_str)
        # 将输入传递给AI
        ai_output = core.call_api(core.create_prompt())
        # 如果发现AI需要执行命令（发现包含成对标签）
        data = database.load_data()
        cmd_start_tag = data['config']['cmd_start_tag']
        cmd_end_tag = data['config']['cmd_end_tag']
        if cmd_start_tag in ai_output and cmd_end_tag in ai_output:
            user_cmd_input = handle_command(ai_output)
        else:
            console.print(rich.markdown.Markdown(ai_output))
            terminal.dividing_line()
            database.add_context('[' + time.ctime() + '][AI] >> ' + ai_output)
            user_cmd_input = None
