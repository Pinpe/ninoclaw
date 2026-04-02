'''
NinoClaw的文件管理API，用于对持久化和配置选项进行操作。
'''


import json
import datetime
import os


# 项目根目录（lib/ 的上一级）
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_path(relative_path: str) -> str:
    '''
    将相对路径解析为基于项目根目录的绝对路径。

    :param relative_path: 相对于项目根目录的路径。
    '''
    return os.path.join(PROJECT_DIR, relative_path)


def format_json_dump(content, file_path: str) -> None:
    '''
    用于在json覆写时提供格式化和设定编码，替代原来的json_dump()。

    :param content: 要覆写的内容。
    :param file_path: 要写入的文件路径（相对于项目根目录）。
    '''
    abs_path = _resolve_path(file_path)
    with open(abs_path, mode='w', encoding='UTF-8') as f:
        json.dump(
            content,
            f,
            ensure_ascii=False,
            indent=4
        )


def load_data() -> dict:
    '''
    加载任何数据。
    '''
    with open(_resolve_path('config.json'), encoding='UTF-8') as f:
        config = json.load(f)
    with open(_resolve_path('env.json'), encoding='UTF-8') as f:
        env = json.load(f)
    with open(_resolve_path('database/context.json'), encoding='UTF-8') as f:
        context = json.load(f)

    # 将配置中的相对路径解析为绝对路径
    if config.get('home_path') and not os.path.isabs(config['home_path']):
        config['home_path'] = _resolve_path(config['home_path'])
    if config.get('prompt_template_path') and not os.path.isabs(config['prompt_template_path']):
        config['prompt_template_path'] = _resolve_path(config['prompt_template_path'])

    return {
        'config': config,
        'env': env,
        'context': context
    }


def add_context(new_context: str) -> None:
    '''
    添加新上下文到数据库。

    :param new_context: 要添加的上下文。
    '''
    context_list = load_data()['context']
    if len(context_list) >= load_data()['config']['context_len']:
        del context_list[0]
    context_list.append(new_context)
    format_json_dump(context_list, 'database/context.json')


def create_diary() -> None:
    '''
    判断有没有今天的日记，如果没有，创建今天的日记。
    '''
    config = load_data()['config']
    diary_path = os.path.join(config['home_path'], 'diary', f'{datetime.date.today()}.md')
    if not os.path.exists(diary_path):
        os.makedirs(os.path.dirname(diary_path), exist_ok=True)
        with open(diary_path, mode='w', encoding='UTF-8') as f:
            f.write(f'# {datetime.date.today()}.md\n\n这是今天的日记，请把今天发生的所有事写下来。')
