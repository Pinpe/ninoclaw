import typer
import subprocess
import re
import os

# 项目根目录
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_OUTPUT = os.path.join(_PROJECT_DIR, 'home')

app = typer.Typer(name="bilibili-downloader", help="下载B站视频/音频")

def extract_bv_id(input_str: str) -> str:
    bv_match = re.search(r"BV[\w]+", input_str, re.IGNORECASE)
    if bv_match:
        return bv_match.group(0)
    return None

def download_bilibili(bv_id: str, output_dir: str = _DEFAULT_OUTPUT, audio_only: bool = True) -> str:
    os.makedirs(output_dir, exist_ok=True)
    video_url = f"https://www.bilibili.com/video/{bv_id}"
    
    if audio_only:
        output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_template, "--no-playlist", video_url]
    else:
        output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
        cmd = ["yt-dlp", "-o", output_template, "--no-playlist", video_url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return "✅ 下载成功！视频URL: " + video_url + "保存位置: " + output_dir
        else:
            error_msg = result.stderr
            if "Connection reset" in error_msg or "Connection refused" in error_msg:
                return "❌ 连接被拒绝，可能是校园网/防火墙屏蔽了B站请尝试切换到其他网络后重试"
            elif "HTTP Error 403" in error_msg:
                return "❌ 403错误，B站拒绝访问可能需要登录或Cookie"
            elif "Video not found" in error_msg:
                return "❌ 视频不存在，请检查BV号是否正确"
            else:
                return "❌ 下载失败: " + error_msg[:200]
    except subprocess.TimeoutExpired:
        return "❌ 下载超时，请检查网络连接后重试"
    except Exception as e:
        return "❌ 发生错误: " + str(e)

@app.command()
def main(
    input: str = typer.Argument(..., help="B站视频链接或BV号"),
    output: str = typer.Option(_DEFAULT_OUTPUT, "--output", "-o", help="输出目录"),
    video: bool = typer.Option(False, "--video", "-v", help="下载完整视频")
):
    bv_id = extract_bv_id(input)
    if not bv_id:
        typer.echo("❌ 无法识别BV号", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"🎵 正在下载: {bv_id}...")
    result = download_bilibili(bv_id, output, audio_only=not video)
    typer.echo(result)

if __name__ == "__main__":
    app()