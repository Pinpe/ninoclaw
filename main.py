'''== 导入模块 =='''
from lib import database
from lib import terminal
from lib import core
import rich.traceback
import rich.markdown
import rich.console
import gnureadline  # 用于修复在Linux下input()函数不好用的问题
import textwrap
import time
import sys
import os


'''== 初始化 =='''
rich.traceback.install(show_locals=True)  # 初始化rich样式的traceback
console        = rich.console.Console()   # 初始化rich的终端对象
user_cmd_input = None
path           = database.load_data()['config']['home_path']
last_cmd       = None


'''== 内部函数 =='''
def handle_commend(ai_output:str) -> str:
    '''
    当发现AI的回复需要执行命令时，在这里处理。

    :param ai_output: AI的输出。
    '''
    global path, user_cmd_input, last_cmd
    # 分割开始标签，分离AI回复内容和命令部分
    ai_content, cmd_part = ai_output.split(database.load_data()['config']['cmd_start_tag'], 1)
    # 分割结束标签，只保留标签内的命令
    cmd = cmd_part.split(database.load_data()['config']['cmd_end_tag'], 1)[0].strip()
    # 打印AI回复并记录上下文
    console.print(rich.markdown.Markdown(ai_content))
    terminal.dividing_line()  # 这里加分割线，让输出更可读，下面的一个也是
    database.add_context(
        f'[{time.ctime()}][AI] >> {ai_content}'
        f'{database.load_data()['config']['cmd_start_tag']}'
        f'{cmd}'
        f'{database.load_data()['config']['cmd_end_tag']}'
    )
    # 判断AI的的命令是否与上一条命令相等，如果是就给AI返回个警告，不是就跳过，以免出现无限循环的问题
    if cmd == last_cmd:
        return '错误：不能执行与上一条相同的命令，如果需要执行，你可以给命令加入多余参数或注释。此机制是为了防止你陷入无限循环。'
    # 校验通过后，即可放心更新last命令
    last_cmd = cmd
    # 处理cd命令，切换工作目录
    if 'cd' in cmd:
        # 去除掉cd、双引号和首尾空格，写在新路径变量
        new_path = os.path.abspath(os.path.join(path, cmd.replace('cd', '').replace('\"', '').strip()))
        # 检查新目录是否是正确的，是的话就替代旧路径，切换目录，不是就报错
        if os.path.isdir(new_path):
            path = new_path
            return f'目录已切换：{path}'
        else:
            return f'错误：目录不存在：{new_path}'
    # 执行命令，返回执行结果
    return core.command_exec(cmd, path)

def title_and_history() -> None:
    '''
    打印主程序的标题和上下文。
    '''
    terminal.clear_screen()
    console.print(textwrap.dedent('''
        [blue]⣿⣆⠱⣝⡵⣝⢅⠙⣿⢕⢕⢕⢕⢝⣥⢒⠅⣿⣿⣿⡿⣳⣌⠪⡪⣡⢑[/blue]    [yellow]███╗   ██╗██╗███╗   ██╗ ██████╗  ██████╗██╗      █████╗ ██╗    ██╗[/yellow]
        [blue]⣿⣿⣦⠹⣳⣳⣕⢅⠈⢗⢕⢕⢕⢕⢕⢈⢆⠟⠋⠉⠁⠉⠉⠁⠈⠼⢐[/blue]    [yellow]████╗  ██║██║████╗  ██║██╔═══██╗██╔════╝██║     ██╔══██╗██║    ██║[/yellow]
        [blue]⢰⣶⣶⣦⣝⢝⢕⢕⠅⡆⢕⢕⢕⢕⢕⣴⠏⣠⡶⠛⡉⡉⡛⢶⣦⡀⠐[/blue]    [yellow]██╔██╗ ██║██║██╔██╗ ██║██║   ██║██║     ██║     ███████║██║ █╗ ██║[/yellow]
        [blue]⡄⢻⢟⣿⣿⣷⣕⣕⣅⣿⣔⣕⣵⣵⣿⣿⢠⣿⢠⣮⡈⣌⠨⠅⠹⣷⡀[/blue]    [yellow]██║╚██╗██║██║██║╚██╗██║██║   ██║██║     ██║     ██╔══██║██║███╗██║[/yellow]
        [blue]⡵⠟⠈⢀⣀⣀⡀⠉⢿⣿⣿⣿⣿⣿⣿⣿⣼⣿⢈⡋⠴⢿⡟⣡⡇⣿⡇[/blue]    [yellow]██║ ╚████║██║██║ ╚████║╚██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝[/yellow]
        [blue]⠁⣠⣾⠟⡉⡉⡉⠻⣦⣻⣿⣿⣿⣿⣿⣿⣿⣿⣧⠸⣿⣦⣥⣿⡇⡿⣰[/blue]    [yellow]╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ [/yellow]
        [blue]⢰⣿⡏⣴⣌⠈⣌⠡⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣬⣉⣉⣁⣄⢖⢕[/blue]
        [blue]⢻⣿⡇⢙⠁⠴⢿⡟⣡⡆⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣵[/blue]                        [b green]版本：3.3.0[/b green]      [b red]作者：Pinpe[/b red]
        [blue]⣄⣻⣿⣌⠘⢿⣷⣥⣿⠇⣿⣿⣿⣿⣿⣿⠛⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿[/blue]
        [blue]⢄⠻⣿⣟⠿⠦⠍⠉⣡⣾⣿⣿⣿⣿⣿⣿⢸⣿⣦⠙⣿⣿⣿⣿⣿⣿⣿[/blue]    输入：[yellow]summary[/yellow] 压缩上下文    [yellow]clear[/yellow] 清除上下文
        [blue]⡑⣑⣈⣻⢗⢟⢞⢝⣻⣿⣿⣿⣿⣿⣿⣿⠸⣿⠿⠃⣿⣿⣿⣿⣿⣿⡿[/blue]          [yellow]exit[/yellow]    退出
        [blue]⡵⡈⢟⢕⢕⢕⢕⣵⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣿⣿⣿⣿⣿⠿⠋⣀[/blue]
    '''))
    # 如果发现有上下文（即上下文不为空），便把上下文打印出来
    if database.load_data()['context'] != []:
        for i in database.load_data()['context']:
            console.print(rich.markdown.Markdown(i))
        # 记得打印这条提示
        console.print('\n[black on blue] 以上为历史消息 [/black on blue]\n')

def user_input_box() -> str | None:
    '''
    用户的输入框，附带命令检查。
    '''
    try:
        user_input = console.input(
            f'[black on yellow] {time.ctime()} [/black on yellow]'
            f'[black on cyan] {path} [/black on cyan][cyan][/cyan]\n'
            '[green]▶[/green] '
        )
    # 如果用户按了Ctrl+C的话就退出，否则traceback就糊脸了
    except KeyboardInterrupt:
        sys.exit(0)
    # 开始判断是否为NinoClaw命令，或是否空白
    if user_input == '':
        print()  # 如果用户输入了空的，用空格隔开，避免把提示符粘在一起
    elif user_input == 'exit':
        sys.exit(0)
    elif user_input == 'summary':
        # 先定义一个空列表，用于存放列表格式的压缩结果，而不是字符串
        summary_list = []
        # 然后通过总结的方式压缩上下文，添加进上面的空列表
        summary_list.append('[摘要] >> ' + core.summary(
            database.load_data()['context'],
            database.load_data()['config']['context_summary_len']
        ))
        # 然后把列表覆写到文件
        database.format_json_dump(summary_list, 'database/context.json')
        # 然后重载标题和上下文的显示
        title_and_history()
        console.print('\n[black on green] 上下文压缩已完成 [/black on green]\n')
    elif user_input == 'clear':
        # 将文件覆写成空列表，这里直接对文件操作，免得让dump()添油加醋
        open('database/context.json', mode='w', encoding='UTF-8').write('[]')
        # 然后重载标题，打印个提示，和上面一样
        title_and_history()
        console.print('\n[black on green] 上下文已清空 [/black on green]\n')
    # 如果既不是命令也不是空白，提前退出函数，返回用户输入
    else:
        return user_input
    return None  # 返回None，会被此函数下面的一个判断（if userinput is None）截获，便不会运行之后的逻辑


'''== 主程序 =='''
if __name__ == '__main__':
    # 首先打印大标题和上下文
    title_and_history()
    # 如果发现没有今天的日记，就创建一个
    database.create_diary()
    # 开始大循环
    while True:
        # 当没有命令输出时，让用户输入，否则则代表有命令返回
        if user_cmd_input is None:
            user_cmd_input = user_input_box()
            # 再检查一遍，如果是None就把循环从头再来
            if user_cmd_input is None: continue
        database.add_context(f'[{time.ctime()}][{path}][用户或返回结果] >> {user_cmd_input}')
        # 将输入（无论是用户的还是命令返回）传递给AI
        ai_output = core.call_api(core.create_prompt())
        # 如果发现AI需要执行命令（发现包含成对标签 ）
        if database.load_data()['config']['cmd_start_tag'] in ai_output \
            and database.load_data()['config']['cmd_end_tag'] in ai_output:
            user_cmd_input = handle_commend(ai_output)
        # 如果不需要执行命令
        else:
            # 直接输出 + 上下文
            console.print(rich.markdown.Markdown(ai_output))
            terminal.dividing_line()
            database.add_context(f'[{time.ctime()}][AI] >> {ai_output}')
            # 重置用户的输入
            user_cmd_input = None