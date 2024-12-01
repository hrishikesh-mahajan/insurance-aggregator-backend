import os
from datetime import datetime
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()


def get_weather_report(lat, lon, timestamp):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = "http://api.openweathermap.org/data/2.5/onecall/timemachine"
    url = "http://api.openweathermap.org/data/2.5/weather"

    params = {"lat": lat, "lon": lon, "dt": timestamp, "appid": api_key}
    params = {"lat": lat, "lon": lon, "appid": api_key}

    response = requests.get(url, params=params)

    print(response.url)

    if response.status_code == 200:
        return response.json()
    else:
        return None


if __name__ == "__main__":
    # Example usage
    latitude = 18.5204
    longitude = 73.8567
    timestamp = int(datetime(2023, 10, 1, 12, 0).timestamp())

    weather_report = get_weather_report(latitude, longitude, timestamp)

    if weather_report:
        pprint(weather_report)
    else:
        print("Failed to get weather report")
