import typer
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import chardet
import urllib3
import time
import random

# 初始化typer应用
app = typer.Typer(
    name="bing-search",
    help="提取Bing搜索结果的文本，将链接转为[文本](链接)格式，仅保留可见文本"
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Bing搜索基础URL
BING_SEARCH_BASE_URL = "https://www.bing.com/search?q="

def format_web_content(url: str) -> str:
    """
    核心函数：请求网页、解析内容、格式化文本（处理链接/按钮）
    """
    # 更真实的浏览器请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.bing.com/"
    }

    # 创建 session 并设置 cookies
    session = requests.Session()

    # 先访问Bing首页获取 cookies
    try:
        session.get("https://www.bing.com/", headers=headers, timeout=10, verify=False)
        time.sleep(random.uniform(0.5, 1.5))  # 随机延迟
    except:
        pass

    try:
        # 发送HTTP请求，超时30秒
        response = session.get(
            url,
            headers=headers,
            timeout=30,
            verify=False  # 忽略SSL证书错误
        )

        # 检查是否被拦截
        if "captcha" in response.text.lower() or "verification" in response.text.lower():
            return "⚠️ Bing验证拦截，请稍后再试或更换搜索关键词"

        # 自动检测编码，解决乱码问题
        detected_encoding = chardet.detect(response.content)["encoding"] or "utf-8"
        response.encoding = detected_encoding

        # 解析HTML
        soup = BeautifulSoup(response.text, "html5lib")

        # 移除非可见文本标签
        for useless_tag in soup(["script", "style", "noscript", "iframe", "svg", "canvas"]):
            useless_tag.decompose()

        # 处理所有<a>标签
        for a_tag in soup.find_all("a", href=True):
            link_text = a_tag.get_text(strip=True) or "链接"
            absolute_href = urljoin(url, a_tag["href"])
            a_tag.string = f"[{link_text}]({absolute_href})"

        # 处理<button>标签
        for btn_tag in soup.find_all("button"):
            btn_text = btn_tag.get_text(strip=True) or "按钮"
            onclick_attr = btn_tag.get("onclick", "")
            # 简单匹配 onclick 中的 URL
            href_match = re.search(r"https?://[^'\s]+", onclick_attr)
            if href_match:
                btn_tag.string = f"[{btn_text}]({href_match.group(0)})"
            else:
                btn_tag.string = btn_text

        # 提取文本并格式化
        raw_text = soup.get_text(separator="\n", strip=True)
        formatted_text = re.sub(r"\n{2,}", "\n", raw_text)

        return formatted_text

    except requests.exceptions.RequestException as e:
        typer.echo(f"❌ 访问网站失败：{str(e)}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ 处理网页内容失败：{str(e)}", err=True)
        raise typer.Exit(code=1)

@app.command()
def main(query: str):
    """
    提取Bing搜索结果的文本内容
    :param query: Bing搜索的关键词
    """
    encoded_query = quote(query)
    bing_search_url = BING_SEARCH_BASE_URL + encoded_query
    content = format_web_content(bing_search_url)
    typer.echo(content)

if __name__ == "__main__":
    app()
