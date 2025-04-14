from config import YANDEX_API_KEY

def generate_map_link(events: list):
    markers = []
    for event in events:
        if "place" in event:
            coords = event["place"]["coords"]
            markers.append(f"{coords['lat']},{coords['lon']},pm2rdl")
    return f"https://static-maps.yandex.ru/1.x/?l=map&pt={'~'.join(markers)}&size=800,400&key={YANDEX_API_KEY}"