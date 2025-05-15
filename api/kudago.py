import requests
from config import KUDAGO_API_URL


def fetch_kudago_events(city: str, category: str = "concert", page_size: int = 5):
    params = {
        "location": city,
        "categories": category,
        "page_size": page_size,
        "fields": "title,place,price,dates,images,site_url"
    }


    try:
        response = requests.get(f"{KUDAGO_API_URL}/events/", params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"KudaGo API Error: {e}")
        return None