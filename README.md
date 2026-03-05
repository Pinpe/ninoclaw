# NinoClaw

NinoClaw 是一个命令行界面的 AI 助手程序，它将大语言模型（LLM）与系统命令执行能力相结合，让你能够在终端中与一个活泼的虚拟少女（pomi）对话，并让她帮你执行 Shell 命令、管理文件等。

此外，也是[Nino](https://github.com/Pinpe/nino-ai-chat)的续作。

## ✨ 功能特点

- **智能对话**：基于 OpenAI API 兼容的模型，支持自定义模型和接口地址。
- **命令执行**：AI 可以通过在消息末尾添加 `command:` 标签调用系统 Shell（支持 Bash/Zsh 等），并返回执行结果。
- **上下文管理**：自动保存最近的对话历史，支持手动压缩（`summary`）或清空（`clear`）上下文，以控制 token 消耗。
- **工作目录保持**：AI 执行的命令会在当前工作目录下运行，支持 `cd` 命令（仅限绝对路径）。
- **记忆机制**：AI 拥有专属的 `MEMORY.md` 文件，可写入重要信息，实现长期记忆。
- **技能扩展**：通过配置文件可自定义可调用的外部命令列表（技能），AI 能通过 `--help` 查看用法。
- **美观输出**：使用 `rich` 库渲染彩色终端输出、Markdown 格式和错误回溯。

## 📦 安装

### 环境要求
- Python 3.8+
- 一个兼容 OpenAI API 的模型接口（如 OpenAI、Azure OpenAI、本地部署的 vLLM 等）

### 安装步骤

1. 克隆仓库或下载源码：
   ```bash
   git clone https://github.com/yourname/ninoclaw.git
   cd ninoclaw
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
   若没有 `requirements.txt`，手动安装以下依赖：
   ```bash
   pip install gnureadline openai rich
   ```
   > **注意**：`gnureadline` 用于改善 Linux 下 `input()` 的体验，Windows 下可尝试安装 `pyreadline3` 或忽略（可能影响回退/历史功能）。

## 🚀 使用方法

在项目目录下运行主程序：
```bash
python main.py
```

启动后将显示 ASCII 艺术标题和最近的历史上下文，然后进入交互模式。

### 内置命令
在输入框（`>>`）中可直接输入以下命令：

| 命令      | 作用                                               |
|-----------|--------------------------------------------------|
| `summary` | 压缩当前上下文，保留重要信息（调用 AI 总结）         |
| `clear`   | 清空所有上下文历史                                 |
| `exit`    | 退出程序                                           |

## 📁 项目结构

```
.
├── main.py                 # 主程序入口
├── core.py                 # 核心功能：API 调用、命令执行、提示词构建、总结
├── database.py             # 数据持久化：读写 JSON 配置和上下文
├── config.json             # 程序配置
├── env.json                # 环境变量（API 密钥）
├── database/
│   └── context.json        # 对话历史上下文
└── README.md               # 本文档
```

## 🛠️ 依赖库

- `openai` —— 调用大语言模型 API
- `rich` —— 终端美化、Markdown 渲染、错误回溯
- `gnureadline` —— （Linux）增强输入行编辑功能

## ⚠️ 已知问题

- 如果 `command:` 标签出现在回复中间（非末尾），会被误解析并尝试执行，因此 AI 在非命令场景下应避免使用该字符串。
- 命令执行使用了 `subprocess` 并加载了 Shell 配置文件，请确保配置文件中没有交互式提示或长期阻塞的命令。
- 当命令执行超时或被用户中断时，会返回相应错误信息。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。请确保代码风格清晰，并更新相应文档。

## 📄 许可证

本项目采用 GPL-3.0 许可证。详见 `LICENSE` 文件。

---

**NinoClaw** —— 让 AI 住在你的终端里，成为你的贴心小助手！🎉