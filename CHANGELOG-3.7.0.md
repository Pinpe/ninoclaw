# NinoClaw 3.7.0 修改清单

## Bug修复

- 将cd命令检测从 `'cd' in cmd`（会误匹配含cd的任意命令如 `echo abcd`）改为专用函数 `_is_cd_command()` 精确判断 [main.py 35-40行]
- 将 `handle_command()` 中的cd检测改为调用 `_is_cd_command(cmd)` [main.py 94行]
- 将 `user_command()` 中的cd检测改为调用 `_is_cd_command(cmd)` [main.py 158行]
- 将 `cd_command()` 中的路径提取从 `cmd.replace('cd', '')` 改为 `cmd.strip()[2:]`，避免命令参数中含cd字样被错误替换 [main.py 51行]
- 将 `create_prompt()` 中的 `eval(f'f"""..."""')` 动态执行改为 `{{placeholder}}` 占位符替换，消除代码注入风险 [core.py 83-97行]
- 将 `terminal.py` 补充缺失的 `import rich.rule`，修复 `dividing_line()` 调用 `rich.rule.Rule` 时的 NameError [terminal.py 9行]
- 将 `weather.py` 中 `f'获取天气失败：{result["error"]}'` 嵌套双引号的f-string改为字符串拼接，修复Python<3.12的语法错误 [weather.py 41行]
- 将 `weather.py` 中 `f"🌍 位置：{result["location"]}..."` 改为字符串拼接 [weather.py 43-47行]
- 将 `main.py` 的 `handle_command()` 中 `f'{database.load_data()['config']['cmd_start_tag']}'` 嵌套引号的f-string改为字符串拼接 [main.py 84-87行]
- 将 `undo()` 添加空列表检查，防止对空上下文执行 `del context_list[-1]` 导致 IndexError [main.py 179行]
- 将 `clear_context()` 从手动 `open().write('[]')` 改为调用 `format_json_dump([])`，统一数据写入方式 [main.py 170行]

## Windows兼容性优化

- 将 `main.py` 初始化区添加Windows下 `pyreadline3` 的导入支持（带ImportError容错） [main.py 20-23行]
- 将 `main.py` 的Linux `gnureadline` 导入也添加ImportError容错，防止未安装时崩溃 [main.py 15-19行]
- 将 `config.json` 的 `shell` 从硬编码 `/usr/bin/fish` 改为 `null`（自动检测） [config.json 11行]
- 将 `config.json` 的 `shell_config` 从硬编码 `/home/pinpe/.config/fish/config.fish` 改为 `null` [config.json 12行]
- 新增 `_get_shell_info()` 函数：Windows自动使用 `cmd.exe`，Linux/macOS使用 `$SHELL` 环境变量 [core.py 101-118行]
- 将 `command_exec()` 分为Windows和Linux两个执行分支：Windows直接 `shell=True` 执行，Linux保留 `source` + `executable` 方式 [core.py 133-155行]
- 将 `main.py` 主程序入口添加 `os.chdir(database.PROJECT_DIR)`，确保无论从哪个目录启动都能找到项目文件 [main.py 239行]

## 路径规范化（消除硬编码路径）

- 新增 `database.PROJECT_DIR` 常量，自动计算项目根目录绝对路径 [database.py 12行]
- 新增 `database._resolve_path()` 函数，将相对路径解析为基于项目根目录的绝对路径 [database.py 15-21行]
- 将 `load_data()` 中的 `open('config.json')` 等相对路径改为 `open(_resolve_path('config.json'))` [database.py 45-50行]
- 将 `load_data()` 新增自动路径解析：如果 `home_path` 和 `prompt_template_path` 是相对路径，自动拼接项目根目录 [database.py 52-56行]
- 将 `config.json` 的 `home_path` 从 `/home/pinpe/文档/代码和项目/ninoclaw/home` 改为 `home` [config.json 22行]
- 将 `config.json` 的 `prompt_template_path` 从 `/home/pinpe/文档/代码和项目/ninoclaw/prompt_template/pomi.md` 改为 `prompt_template/pomi.md` [config.json 23行]
- 将 `create_diary()` 中的日记路径改为通过 `os.path.join(config['home_path'], 'diary', ...)` 动态拼接，并添加 `os.makedirs(exist_ok=True)` 自动创建目录 [database.py 82-87行]
- 将 `get_llm.py` 的API密钥路径从硬编码 `/home/pinpe/.../env.json` 改为 `os.path.join(_PROJECT_DIR, 'env.json')` [get_llm.py 8,16-19行]
- 将 `get_llm.py` 的 `base_url` 从硬编码 `'https://www.packyapi.com/v1'` 改为从 `config.json` 读取 [get_llm.py 21-24,37行]
- 将 `get_llm.py` 的模型从硬编码 `"minimax-m2.5"` 改为从 `config.json` 读取 `config['model']` [get_llm.py 41行]
- 将 `vision.py` 的API密钥路径从硬编码 `/home/pinpe/.../env.json` 改为 `os.path.join(_PROJECT_DIR, 'env.json')` [vision.py 10,45-47行]
- 将 `ocr.py` 的API密钥路径从硬编码 `/home/pinpe/.../env.json` 改为 `os.path.join(_PROJECT_DIR, 'env.json')` [ocr.py 10,41-43行]
- 将 `weather.py` 的API密钥加载从模块级硬编码路径改为 `_load_env()` 函数动态读取 [weather.py 8-14,19行]
- 将 `bilibili_download.py` 的默认输出目录从硬编码 `/home/pinpe/.../home` 改为 `os.path.join(_PROJECT_DIR, 'home')` [bilibili_download.py 7-8,18,52行]

## 代码质量改进

- 将 `core.py` 的 `command_exec(input, path)` 参数名 `input` 改为 `cmd`，不再遮蔽Python内建函数 `input()` [core.py 122行]
- 将 `core.py` 的 `summary(content, len)` 参数名 `len` 改为 `max_len`，不再遮蔽Python内建函数 `len()` [core.py 169行]
- 将 `database.py` 的 `load_data()` 返回类型标注从 `dict[str]`（无效）改为 `dict` [database.py 41行]
- 将 `database.py` 的 `format_json_dump()` 从 `open()` 裸调用改为 `with open() as f` 语句，确保文件句柄正确关闭 [database.py 32-38行]
- 将 `database.py` 的 `load_data()` 三处 `json.load(open(...))` 改为 `with open() as f` + `json.load(f)` [database.py 45-50行]
- 将 `database.py` 的 `create_diary()` 从 `open().read()` 和 `open().write()` 改为 `with` 语句 [database.py 86-87行]
- 将 `core.py` 的 `call_api()` 中重复调用 `database.load_data()` 改为一次调用缓存到 `data` 变量 [core.py 29行]
- 将 `main.py` 的 `summary()` 中重复调用 `database.load_data()` 改为一次调用缓存到 `data` 变量 [main.py 130-133行]
- 将 `main.py` 的 `handle_command()` 中重复调用 `database.load_data()` 改为一次调用缓存到 `data` 变量 [main.py 73-75行]

## 模板系统重构

- 将 `pomi.md` 模板中的Python表达式占位符（如 `{database.load_data()['config']['home_path']}`）全部改为简单的 `{{placeholder}}` 格式 [prompt_template/pomi.md 全文]
- 将 `void.md` 模板做同样的占位符格式替换 [prompt_template/void.md 全文]
- 将 `core.py` 的 `create_prompt()` 从 `eval(f'f"""..."""')` 改为字典驱动的占位符替换循环 [core.py 83-97行]

## Git和项目规范化

- 将 `.gitignore` 从5行扩充至28行，覆盖 `*.py[cod]`、`*.egg-info/`、`dist/`、`build/`、`.env`、`*.key`、`.idea/`、`*.swp`、`.DS_Store`、`Thumbs.db`、`desktop.ini`、`home/diary/` 等 [.gitignore 全文]
- 新增 `.gitattributes` 文件，统一仓库换行符为LF，标记二进制文件类型 [.gitattributes 全文]
- 将 `.editorconfig` 添加 `end_of_line = lf` 规范 [.editorconfig 9行]
- 将 `.editorconfig` 的 `insert_final_newline` 从 `false` 改为 `true` [.editorconfig 12行]
- 将 `requirements.txt` 移除标准库模块 `subprocess` 和 `urllib` [requirements.txt 全文]
- 将 `requirements.txt` 添加平台条件依赖：`pyreadline3; sys_platform == "win32"` 和 `gnureadline; sys_platform != "win32"` [requirements.txt 9-10行]

## 版本号

- 将 `main.py` 标题显示的版本号从 `3.6.0` 改为 `3.7.0` [main.py 112行]
