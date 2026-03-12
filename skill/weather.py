import typer
import requests
import json

app = typer.Typer(name="weather", help="获取指定城市的天气信息（使用心知天气API）")

WEATHER_API_KEY = json.load(open('/home/pinpe/文档/代码和项目/ninoclaw/env.json', encoding='UTF-8'))['weather_api_key']
WEATHER_API_URL = "https://api.seniverse.com/v3/weather/now.json"

def get_weather(location: str) -> dict:
    try:
        r = requests.get(WEATHER_API_URL, params={"key": WEATHER_API_KEY, "location": location}, timeout=10).json()
        data = r["results"][0]["now"]
        return {"location": r["results"][0]["location"]["name"], "text": data["text"], "temperature": data["temperature"], "humidity": data.get("humidity","暂无"), "wind_direction": data.get("wind_direction","暂无"), "wind_scale": data.get("wind_scale","暂无")}
    except Exception as e:
        return {"error": str(e)}

@app.command()
def main(location: str):
    if not location:
        typer.echo("请提供城市名称，例如：weather 北京", err=True)
        raise typer.Exit(code=1)
    result = get_weather(location)
    if "error" in result:
        typer.echo(f"获取天气失败：{result["error"]}", err=True)
        raise typer.Exit(code=1)
    output = f"🌍 位置：{result["location"]}\n🌤️ 天气：{result["text"]}\n🌡️ 温度：{result["temperature"]}°C\n"
    typer.echo(output)

if __name__ == "__main__":
    app()
