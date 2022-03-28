import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_URL = f"https://api.openweathermap.org/data/2.5/onecall?lat={os.getenv('LOCATION_LAT')}&lon={os.getenv('LOCATION_LONG')}&units=imperial&exclude=minutely&appid={os.getenv('WEATHER_API_KEY')}"

def get_json() -> str:
    return json.loads(requests.get(API_URL).text)

if __name__ == "__main__":
    print(requests.get(API_URL).text)