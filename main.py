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
    import gnureadline  # 用于修复在Linux下input()函数不好用的问题，导入下就能用
rich.traceback.install(show_locals=True)  # 初始化rich样式的traceback
console        = rich.console.Console()   # 初始化rich的终端对象
user_cmd_input = None
path           = database.load_data()['config']['home_path']
last_cmd       = None


'''== 内部函数 =='''
def cd_command(cmd):
    '''
    在命令交给命令执行器之前，如果发现输入的命令为cd，则可以执行这个特制的命令，更新path，不交给命令执行器。
    
    :param cmd: 要执行的命令
    '''
    global path
    # 去除掉cd、双引号和首尾空格，得到目标路径
    target = cmd.replace('cd', '').replace('\"', '').strip()
    # 处理 ~ 展开：如果目标路径以 ~ 开头，则替换为自定义的 HOME_DIR
    if target.startswith('~'):
        target = database.load_data()['config']['home_path'] + target[1:]   # 保留 ~ 后面的部分（如 /documents）
    # 拼接当前路径并获取绝对路径
    new_path = os.path.abspath(os.path.join(path, target))
    # 检查新目录是否存在且为目录
    if os.path.isdir(new_path):
        path = new_path
        return f'目录已切换：{path}'
    else:
        return f'错误：目录不存在：{new_path}'


def handle_command(ai_output: str) -> str:
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
        return cd_command(cmd)
    # 执行命令，返回执行结果
    return core.command_exec(cmd, path)

def title_and_history() -> None:
    '''
    打印主程序的标题和上下文。
    '''
    console.clear()
    console.print(textwrap.dedent('''
        [cyan]⣿⣆⠱⣝⡵⣝⢅⠙⣿⢕⢕⢕⢕⢝⣥⢒⠅⣿⣿⣿⡿⣳⣌⠪⡪⣡⢑[/cyan]    [yellow]███╗   ██╗██╗███╗   ██╗ ██████╗  ██████╗██╗      █████╗ ██╗    ██╗[/yellow]
        [cyan]⣿⣿⣦⠹⣳⣳⣕⢅⠈⢗⢕⢕⢕⢕⢕⢈⢆⠟⠋⠉⠁⠉⠉⠁⠈⠼⢐[/cyan]    [yellow]████╗  ██║██║████╗  ██║██╔═══██╗██╔════╝██║     ██╔══██╗██║    ██║[/yellow]
        [cyan]⢰⣶⣶⣦⣝⢝⢕⢕⠅⡆⢕⢕⢕⢕⢕⣴⠏⣠⡶⠛⡉⡉⡛⢶⣦⡀⠐[/cyan]    [yellow]██╔██╗ ██║██║██╔██╗ ██║██║   ██║██║     ██║     ███████║██║ █╗ ██║[/yellow]
        [cyan]⡄⢻⢟⣿⣿⣷⣕⣕⣅⣿⣔⣕⣵⣵⣿⣿⢠⣿⢠⣮⡈⣌⠨⠅⠹⣷⡀[/cyan]    [yellow]██║╚██╗██║██║██║╚██╗██║██║   ██║██║     ██║     ██╔══██║██║███╗██║[/yellow]
        [cyan]⡵⠟⠈⢀⣀⣀⡀⠉⢿⣿⣿⣿⣿⣿⣿⣿⣼⣿⢈⡋⠴⢿⡟⣡⡇⣿⡇[/cyan]    [yellow]██║ ╚████║██║██║ ╚████║╚██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝[/yellow]
        [cyan]⠁⣠⣾⠟⡉⡉⡉⠻⣦⣻⣿⣿⣿⣿⣿⣿⣿⣿⣧⠸⣿⣦⣥⣿⡇⡿⣰[/cyan]    [yellow]╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ [/yellow]
        [cyan]⢰⣿⡏⣴⣌⠈⣌⠡⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣬⣉⣉⣁⣄⢖⢕[/cyan]
        [cyan]⢻⣿⡇⢙⠁⠴⢿⡟⣡⡆⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣵[/cyan]                        [b green]版本：3.5.0[/b green]      [b red]作者：Pinpe[/b red]
        [cyan]⣄⣻⣿⣌⠘⢿⣷⣥⣿⠇⣿⣿⣿⣿⣿⣿⠛⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿[/cyan]
        [cyan]⢄⠻⣿⣟⠿⠦⠍⠉⣡⣾⣿⣿⣿⣿⣿⣿⢸⣿⣦⠙⣿⣿⣿⣿⣿⣿⣿[/cyan]          输入：    [yellow]summary[/yellow] 压缩上下文       [yellow]clear[/yellow] 清除上下文
        [cyan]⡑⣑⣈⣻⢗⢟⢞⢝⣻⣿⣿⣿⣿⣿⣿⣿⠸⣿⠿⠃⣿⣿⣿⣿⣿⣿⡿[/cyan]                    [yellow]command[/yellow] 执行Shell命令    [yellow]exit[/yellow]  退出
        [cyan]⡵⡈⢟⢕⢕⢕⢕⣵⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣿⣿⣿⣿⣿⠿⠋⣀[/cyan]
    '''))
    # 如果发现有上下文（即上下文不为空），便把上下文打印出来
    if database.load_data()['context'] != []:
        for i in database.load_data()['context']:
            console.print(rich.markdown.Markdown(i))
            terminal.dividing_line()
        # 记得打印这条提示
        console.print('\n[black on blue] 以上为历史消息 [/black on blue]\n')

def summary() -> None:
    '''
    执行用户输入的summary命令。
    '''
    # 首先将上下文载入到变量里，方便修改
    context_list = database.load_data()['context']
    # 然后截取[0:config]条，生成摘要，并且插入到[0]中（最顶部）
    context_list.insert(0, '[摘要] >> ' + core.summary(
        database.load_data()['context'][:database.load_data()['config']['context_summary_input_len']],
        database.load_data()['config']['context_summary_len']
    ))
    # 然后删除，除了摘要的config条内容
    del context_list[1:database.load_data()['config']['context_summary_input_len']]
    database.format_json_dump(context_list, 'database/context.json')
    # 然后重载标题和上下文的显示
    title_and_history()
    console.print('\n[black on green] 上下文压缩已完成 [/black on green]\n')

def user_command() -> None:
    '''
    执行用户输入的command命令。
    '''
    try:
        cmd = console.input('[blue]$[/blue] ')
    except KeyboardInterrupt:
        sys.exit(0)
    # 如果命令是空白的，则回调到本函数，重新让用户输入
    if cmd == '':
        print()  # 这里加个换行，好看点
    # 先把用户输入的命令添加到上下文
    database.add_context(f'[{time.ctime()}][{path}][用户自己执行命令] >> {cmd}')
    # 处理cd命令，切换工作目录
    if 'cd' in cmd:
        cmd_output = cd_command(cmd)
    else:
        # 执行命令，返回执行结果
        cmd_output = core.command_exec(cmd, path)
    # 然后打印出运行结果并保存在上下文
    console.print(cmd_output)
    terminal.dividing_line()
    database.add_context(f'[{time.ctime()}][{path}][用户或返回结果] >> {cmd_output}')

def clear_context():
    '''
    执行用户输入的clear命令。
    '''
    # 将文件覆写成空列表，这里直接对文件操作，免得让dump()添油加醋
    open('database/context.json', mode='w', encoding='UTF-8').write('[]')
    # 然后重载标题，打印个提示，和上面一样
    title_and_history()
    console.print('\n[black on green] 上下文已清空 [/black on green]\n')

def user_input_box() -> str | None:
    '''
    用户的输入框，附带命令检查。
    '''
    try:
        user_input = console.input(
            f'[black on yellow] {time.ctime()} [/black on yellow]'
            f'[yellow on blue][/yellow on blue]'
            f'[black on blue] {path} [/black on blue][blue][/blue]\n'
            f'[green]▶[/green] '
        )
    # 如果用户按了Ctrl+C的话就退出，否则traceback就糊脸了，下面的也是
    except KeyboardInterrupt:
        sys.exit(0)
    # 这个表定义了用户输入什么字段就执行什么（内部命令），只能用函数的引用和lambda函数
    cmd_table = {
        ''       : lambda: print(), # 如果用户输入了空的，用空格隔开，避免把提示符粘在一起
        'exit'   : lambda: sys.exit(0),
        'summary': summary,
        'clear'  : clear_context,
        'command': user_command,
    }
    if user_input in cmd_table:  # 当发现用户输入是上表里面的值，就执行这个函数
        cmd_table[user_input]()     # 当然，虽然这个写法有点抽象，但的确能执行
    else:
        # 如果既不是命令也不是空白，提前退出函数，返回用户输入
        return user_input
    return None  # 返回None，会被此函数下面的一个判断（if userinput is None）截获，便不会运行之后的逻辑
                    # 只要不提前返回user_input就没事，有这个兜着


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
        # 如果发现AI需要执行命令（发现包含成对标签）
        if database.load_data()['config']['cmd_start_tag'] in ai_output \
            and database.load_data()['config']['cmd_end_tag'] in ai_output:
            user_cmd_input = handle_command(ai_output)
        # 如果不需要执行命令
        else:
            # 直接输出 + 上下文
            console.print(rich.markdown.Markdown(ai_output))
            terminal.dividing_line()
            database.add_context(f'[{time.ctime()}][AI] >> {ai_output}')
            # 重置用户的输入
            user_cmd_input = None