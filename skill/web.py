import typer
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import chardet
import urllib3

# 初始化typer应用
app = typer.Typer(
    name="web-text-fetcher",
    help="提取网页文本，将链接/按钮转为[文本](链接)格式，仅保留可见文本"
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def format_web_content(url: str) -> str:
    """
    核心函数：请求网页、解析内容、格式化文本（处理链接/按钮）
    """
    # 模拟浏览器请求头，避免被反爬
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }

    try:
        # 发送HTTP请求，超时30秒
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
            verify=False  # 忽略SSL证书错误（新手友好）
        )

        # 自动检测编码，解决乱码问题
        detected_encoding = chardet.detect(response.content)["encoding"] or "utf-8"
        response.encoding = detected_encoding

        # 解析HTML（使用html5lib兼容各种网页结构）
        soup = BeautifulSoup(response.text, "html5lib")

        # 移除非可见文本标签（script/style等）
        for useless_tag in soup(["script", "style", "noscript", "iframe", "svg", "canvas"]):
            useless_tag.decompose()

        # 处理所有<a>标签：转为[文本](链接)格式
        for a_tag in soup.find_all("a", href=True):
            # 提取链接文本（去空格，无文本则默认"链接"）
            link_text = a_tag.get_text(strip=True) or "链接"
            # 相对链接转绝对链接（agent可直接访问）
            absolute_href = urljoin(url, a_tag["href"])
            # 替换a标签内容为格式化链接
            a_tag.string = f"[{link_text}]({absolute_href})"

        # 处理<button>标签：提取文本+onclick中的链接（如有）
        for btn_tag in soup.find_all("button"):
            btn_text = btn_tag.get_text(strip=True) or "按钮"
            onclick_attr = btn_tag.get("onclick", "")
            
            # 简单提取onclick中的链接（匹配window.open/跳转等场景）
            href_match = re.search(r'["\'](https?://[^"\']+)["\']', onclick_attr)
            if href_match:
                btn_tag.string = f"[{btn_text}]({href_match.group(1)})"
            else:
                btn_tag.string = btn_text

        # 提取文本并格式化（换行分隔，去多余空行）
        raw_text = soup.get_text(separator="\n", strip=True)
        # 把多个连续换行转为单个换行，保证格式有序
        formatted_text = re.sub(r'\n{2,}', '\n\n', raw_text)

        return formatted_text

    except requests.exceptions.RequestException as e:
        typer.echo(f"❌ 访问网站失败：{str(e)}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ 处理网页内容失败：{str(e)}", err=True)
        raise typer.Exit(code=1)

@app.command()
def main(url: str):
    """
    提取指定网址的文本内容（示例：python web.py https://pinpe.top）
    :param url: 要访问的网站地址（需包含http/https）
    """
    # 获取格式化后的文本
    content = format_web_content(url)
    # 输出文本（强制UTF-8编码，避免乱码）
    typer.echo(content)

if __name__ == "__main__":
    app()