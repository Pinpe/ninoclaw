'''
NinoClaw的文件管理API，用于对持久化和配置选项进行操作。
'''


import json


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
    if len(context_list) == load_data()['config']['context_len']:  # 保留多少上下文条数，在config里设定
        del context_list[0]
    context_list.append(new_context)
    format_json_dump(context_list, 'database/context.json')