"""直接测试 OpenWeatherMap API"""
import requests

API_KEY = "a0dd699ea6521a4b28c22ff9cf9896c7"

print("=" * 60)
print("测试 OpenWeatherMap API 连接")
print("=" * 60)

# 测试1: 直接HTTP请求
print("\n【测试1】直接API调用（苏州）")
try:
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "Suzhou,CN",
        "appid": API_KEY,
        "units": "metric",
        "lang": "zh_cn"
    }
    
    print(f"  请求URL: {url}")
    print(f"  参数: {params}")
    
    response = requests.get(url, params=params, timeout=10)
    print(f"  状态码: {response.status_code}")
    print(f"  响应头: {dict(response.headers)}")
    
    data = response.json()
    print(f"  响应内容: {data}")
    
    if response.status_code == 200 and data.get("cod") == 200:
        temp = data["main"]["temp"]
        weather = data["weather"][0]["main"]
        print(f"\n  ✅ 成功! 苏州当前天气: {temp}°C, {weather}")
    else:
        print(f"\n  ❌ 失败: {data}")
        
except Exception as e:
    print(f"  ❌ 异常: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 测试北京
print("\n【测试2】测试北京")
try:
    params = {
        "q": "Beijing,CN",
        "appid": API_KEY,
        "units": "metric"
    }
    
    response = requests.get(url, params=params, timeout=10)
    print(f"  状态码: {response.status_code}")
    
    data = response.json()
    
    if response.status_code == 200:
        temp = data["main"]["temp"]
        weather = data["weather"][0]["main"]
        print(f"  ✅ 成功! 北京当前天气: {temp}°C, {weather}")
    else:
        print(f"  ❌ 失败: {data}")
        
except Exception as e:
    print(f"  ❌ 异常: {e}")

# 测试3: 验证环境变量加载
print("\n【测试3】验证项目配置")
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from app.core.config import settings
    
    print(f"  配置的API KEY: {settings.OPENWEATHER_API_KEY}")
    print(f"  KEY长度: {len(settings.OPENWEATHER_API_KEY)}")
    
    if settings.OPENWEATHER_API_KEY == API_KEY:
        print(f"  ✅ 环境变量加载正确")
    else:
        print(f"  ❌ 环境变量不匹配!")
        print(f"  预期: {API_KEY}")
        print(f"  实际: {settings.OPENWEATHER_API_KEY}")
        
except Exception as e:
    print(f"  ❌ 配置加载失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
