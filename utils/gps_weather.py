import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()


def get_weather_report(lat, lon, timestamp):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = "http://api.openweathermap.org/data/2.5/onecall/timemachine"

    params = {"lat": lat, "lon": lon, "dt": timestamp, "appid": api_key}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None


if __name__ == "__main__":
    # Example usage
    latitude = 37.7749
    longitude = -122.4194
    timestamp = int(datetime(2023, 10, 1, 12, 0).timestamp())

    weather_report = get_weather_report(latitude, longitude, timestamp)

    if weather_report:
        print(weather_report)
    else:
        print("Failed to get weather report")
