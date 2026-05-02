'''
终端输出API，用于封装和补充原本rich的功能。
'''


from textual.containers import Vertical, Horizontal
from textual.widgets    import Label, Button
from rich.progress      import Progress, SpinnerColumn, TextColumn
from textual.app        import App, ComposeResult
from functools          import wraps
from lib                import database
import rich.console
import rich.rule



# 初始化rich的终端对象
console = rich.console.Console()


def command_proceessed(loading_text: str) -> None:
    '''
    给某个函数打印“加载中”提示，当函数完成时自动消失，此外这是一个装饰器。

    :param loading_text: 提示文案，可以填“加载中...”、“保存中...”什么的。
    '''
    # 这里是来自另一个项目Nihongo的，我原样搬了过来
    def get_func(func):
        @wraps(func)
        def execute(*args, **kwargs):
            with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True) as progress:
                progress.add_task(description=loading_text, total=None)
                result = func(*args, **kwargs)
            return result
        return execute
    return get_func


def dividing_line(style: str | None = 'green', characters: str = '=') -> None:
    '''
    分割线，打印出可以适配终端长度的一条线。
    '''
    console.print(rich.rule.Rule(style=style, characters=characters))
    print()


def send_notify(text: str, title: str = 'NinoClaw') -> None:
    '''
    若终端兼容，会在系统通知栏显示通知。

    :param text: 通知内容。
    :param title: 通知标题。
    '''
    if database.load_data()['config']['show_notify'] == True:
        print(f'\x1b]777;notify;{title};{text}\x1b\\' , end='')


def confirm_modal(message: str = "确认执行此操作？", yes: str = '确认', no: str = '取消') -> bool:
    '''
    全屏TUI确认模态框（Y/N）（使用AI编写）

    :param message: 模态框提示文字
    :param yes: 确认选项的文本
    :param no: 取消选项的文本
    '''
    class ModalApp(App[bool]):
        # CSS 样式：居中、边框、间距
        CSS = """
        Screen { align: center middle; }
        #dialog { width: auto; height: auto; padding: 1 4; }
        Horizontal { width: auto; height: auto; margin-top: 2; align: center middle; }
        Button { margin: 0 2; }
        """
        def compose(self) -> ComposeResult:
            with Vertical(id="dialog"):
                yield Label(message)
                with Horizontal():
                    yield Button(yes, variant="success", id="yes")
                    yield Button(no, variant="error", id="no")
        def on_button_pressed(self, event: Button.Pressed) -> None:
            # 点击按钮后退出全屏，并返回布尔值
            self.exit(event.button.id == "yes")
    return ModalApp().run()