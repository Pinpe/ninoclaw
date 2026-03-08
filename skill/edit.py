#!/usr/bin/env python3
import typer

app = typer.Typer()

@app.command()
def main(
    file_path: str = typer.Argument(..., help="要覆盖写入的文件路径"),
    file_content: str = typer.Argument(..., help="要写入文件的新内容（输入 \n 表示实际换行符，输入 \\n 表示字面量反斜杠n）")
):
    """
    将新的文件内容覆盖写入到指定文件路径。

    支持多行写入：`python edit.py <路径> "这是行1
    这是行2
    这是行3"`

    转义说明：
    - 输入 \n 会转换为实际换行符
    - 输入 \\n 会保留为字面量 \n（不转换）
    """
    try:
        # 处理转义：将 \n 解析为换行符，\\n 保留为 \n
        processed_content = file_content.encode('raw_unicode_escape').decode('unicode_escape')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        typer.echo(f"成功将内容写入 {file_path}")
    except Exception as e:
        typer.echo(f"写入文件时出错: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
