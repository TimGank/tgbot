import requests
from config import KUDAGO_API_KEY

def get_events(city: str, category: str = "concert"):
    url = "https://kudago.com/public-api/v1.4/events/"
    params = {
        "location": city,
        "categories": category,
        "api_key": KUDAGO_API_KEY,
        "fields": "title,place,price,dates"
    }
    response = requests.get(url, params=params)
    return response.json().get("results", [])