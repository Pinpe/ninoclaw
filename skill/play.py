import typer
import subprocess
import sys
import os
import signal
from pathlib import Path

app = typer.Typer(help="音频播放工具，新开终端窗口播放音频（基于ffplay）")

def play_audio_in_new_window(audio_path: str):
    """
    新终端窗口内的核心逻辑：显示信息 + 调用ffplay播放 + 回车停止
    """
    audio_file = Path(audio_path).absolute()
    
    # 1. 校验文件是否存在
    if not audio_file.exists():
        print(f"错误：文件 {audio_file} 不存在！")
        input("\n按下回车键关闭窗口...")
        sys.exit(1)
    
    # 2. 显示文件信息
    file_size = round(audio_file.stat().st_size / 1024 / 1024, 2)
    print("=" * 50)
    print(f"正在播放：{audio_file.name}")
    print(f"文件路径：{audio_file}")
    print(f"文件大小：{file_size} MB")
    print("=" * 50)
    print("\n按下回车键停止播放并关闭窗口...")
    
    # 3. 启动ffplay播放音频（静音输出，不显示ffplay自身窗口）
    ffplay_cmd = [
        "ffplay",
        "-nodisp",  # 不显示视频窗口（纯音频）
        "-autoexit",  # 播放完自动退出
        "-loglevel", "quiet",  # 屏蔽ffplay日志
        str(audio_file)
    ]
    
    ffplay_process = subprocess.Popen(
        ffplay_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if sys.platform != "win32" else None  # Linux/macOS设置进程组
    )
    
    # 4. 等待用户按回车，停止播放
    try:
        input()  # 阻塞等待回车
    except KeyboardInterrupt:
        pass
    
    # 5. 终止ffplay进程（Linux/macOS杀进程组，Windows杀进程）
    if sys.platform == "win32":
        ffplay_process.terminate()
    else:
        os.killpg(os.getpgid(ffplay_process.pid), signal.SIGTERM)
    
    ffplay_process.wait()  # 等待进程退出
    sys.exit(0)

def get_new_terminal_command(script_path: str, audio_path: str) -> list:
    """生成跨平台打开新终端的命令（适配Linux/macOS/Windows）"""
    script_path = f'"{script_path}"' if " " in script_path else script_path
    audio_path = f'"{audio_path}"' if " " in audio_path else audio_path
    
    if sys.platform == "win32":
        return [
            "start", "cmd", "/k",
            f'python {script_path} play-in-window {audio_path}'
        ]
    elif sys.platform == "darwin":
        osascript_cmd = (
            f'tell application "Terminal" to do script '
            f'"cd {os.getcwd()}; python3 {script_path} play-in-window {audio_path}"'
        )
        return ["osascript", "-e", osascript_cmd]
    else:
        # Linux（gnome-terminal）
        return [
            "kitty", "--", "bash", "-c",
            f'python3 {script_path} play-in-window {audio_path}; exec bash'
        ]

@app.command()
def play(audio_path: str):
    """主命令：play <音频文件路径>（新开窗口播放，不阻塞原终端）"""
    script_path = Path(__file__).absolute()
    new_terminal_cmd = get_new_terminal_command(str(script_path), audio_path)
    
    # 启动新终端进程（不阻塞原终端）
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                " ".join(new_terminal_cmd),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            subprocess.Popen(
                new_terminal_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        print(f"✅ 已启动音频播放窗口：{audio_path}")
    except Exception as e:
        typer.echo(f"❌ 启动播放窗口失败：{e}", err=True)

@app.command(hidden=True)
def play_in_window(audio_path: str):
    """隐藏命令：仅用于新终端窗口内部调用"""
    play_audio_in_new_window(audio_path)

if __name__ == "__main__":
    app()