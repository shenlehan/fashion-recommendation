import requests

def get_weather_data(api_key, location):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def extract_weather_info(weather_data):
    if weather_data:
        main = weather_data.get('main', {})
        weather = weather_data.get('weather', [{}])[0]
        
        temperature = main.get('temp')
        humidity = main.get('humidity')
        description = weather.get('description')
        
        return {
            'temperature': temperature,
            'humidity': humidity,
            'description': description
        }
    return None

def get_weather(location, api_key):
    weather_data = get_weather_data(api_key, location)
    return extract_weather_info(weather_data)