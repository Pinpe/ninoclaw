'''
NinoClaw的文件管理API，用于对持久化和配置选项进行操作。
'''


import json
import datetime


def format_json_dump(content, file_path):
    '''
    用于在json**覆写**时提供格式化和设定编码，替代原来的json_dump()。

    :param content: 要**覆写**的内容。
    :param file_path: 要写入的文件路径。
    '''
    json.dump(
        content,
        open(file_path, mode='w', encoding='UTF-8'),
        ensure_ascii = False,
        indent       = 4
    )


def load_data() -> dict[str]:
    '''
    加载任何数据。
    '''
    return {
        'config':  json.load(open('config.json', encoding='UTF-8')),
        'env':     json.load(open('env.json', encoding='UTF-8')),
        'context': json.load(open('database/context.json', encoding='UTF-8'))
    }


def add_context(new_context: str) -> None:
    '''
    添加新上下文到数据库。

    :param new_context: 要添加的上下文。
    '''
    context_list = load_data()['context']
    if len(context_list) >= load_data()['config']['context_len']:  # 保留多少上下文条数，在config里设定
        del context_list[0]
    context_list.append(new_context)
    format_json_dump(context_list, 'database/context.json')


def create_diary() -> None:
    '''
    判断有没有今天的日记，如果没有，创建今天的日记。
    '''
    # 先判断有没有今天的日记：打开今天的日记文件，如果无法打开代表没有创建
    try:
        open(f'home/diary/{datetime.date.today()}.md', mode='r', encoding='UTF-8').read()
    # 如果没有，创建日记文件，并且写入日记空模板
    except FileNotFoundError:
        open(f'home/diary/{datetime.date.today()}.md', mode='w', encoding='UTF-8') \
            .write(f'# {datetime.date.today()}.md\n\n这是今天的日记，请把今天发生的所有事写下来。')