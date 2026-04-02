'''
终端输出API，用于封装和补充原本rich的功能。
'''


from rich.progress import Progress, SpinnerColumn, TextColumn
from functools     import wraps
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


def dividing_line() -> None:
    '''
    分割线，打印出可以适配终端长度的一条线。
    '''
    console.print(rich.rule.Rule(characters='='))
    print()