import requests
from typing import Dict, Any


def get_weather_by_city(city: str) -> Dict[str, Any]:
  """
  预留接口：获取城市天气
  实际开发中需配置 API KEY
  """
  # 示例调用 OpenWeatherMap API（需注册获取 KEY）
  # api_key = "YOUR_API_KEY"
  # url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
  # resp = requests.get(url).json()

  # 开发阶段 mock 返回
  return {
    "temperature": 25,
    "weather": "sunny",
    "humidity": 60
  }