import requests
from config import KUDAGO_API_URL
from typing import Optional, List, Dict

def fetch_kudago_events(
    city: str,
    category: str = "concert",
    page_size: int = 5
) -> Optional[List[Dict]]:
    """
    Поиск событий через KudaGo API
    Документация: https://docs.kudago.com/api/#operation/events-list
    """
    endpoint = f"{KUDAGO_API_URL}/events/"
    params = {
        "location": city,  # Например: "msk", "spb"
        "categories": category,
        "page_size": page_size,
        "fields": "id,title,place,price,dates,description,images,site_url"
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"KudaGo API Error: {e}")
        return None


def handle_kudago_errors(response):
    if response.status_code == 400:
        raise ValueError("Неверные параметры запроса")
    elif response.status_code == 429:
        raise ValueError("Слишком много запросов")
    elif response.status_code >= 500:
        raise ValueError("Ошибка сервера KudaGo")

