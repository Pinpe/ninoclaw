import typer
import requests
import json
import os

app = typer.Typer(name="weather", help="获取指定城市的天气信息（使用心知天气API）")

# 项目根目录
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_env():
    env_path = os.path.join(_PROJECT_DIR, 'env.json')
    with open(env_path, encoding='UTF-8') as f:
        return json.load(f)

WEATHER_API_URL = "https://api.seniverse.com/v3/weather/now.json"

def get_weather(location: str) -> dict:
    api_key = _load_env()['weather_api_key']
    try:
        r = requests.get(WEATHER_API_URL, params={"key": api_key, "location": location}, timeout=10).json()
        data = r["results"][0]["now"]
        return {
            "location": r["results"][0]["location"]["name"],
            "text": data["text"],
            "temperature": data["temperature"],
            "humidity": data.get("humidity", "暂无"),
            "wind_direction": data.get("wind_direction", "暂无"),
            "wind_scale": data.get("wind_scale", "暂无")
        }
    except Exception as e:
        return {"error": str(e)}

@app.command()
def main(location: str):
    if not location:
        typer.echo("请提供城市名称，例如：weather 北京", err=True)
        raise typer.Exit(code=1)
    result = get_weather(location)
    if "error" in result:
        typer.echo("获取天气失败：" + result["error"], err=True)
        raise typer.Exit(code=1)
    output = (
        "位置：" + result["location"] + "\n"
        "天气：" + result["text"] + "\n"
        "温度：" + result["temperature"] + "°C\n"
    )
    typer.echo(output)

if __name__ == "__main__":
    app()
