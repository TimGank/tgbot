from flask import Flask, request, jsonify
from database.crud import get_user, update_user_city
from api.event_providers import get_events
from api.maps import generate_map_link
from database.session import Base, engine
from sqlalchemy import create_engine
from tg.bot import main
print("SQLAlchemy работает!")

app = Flask(__name__)

# Создание таблиц
Base.metadata.create_all(bind=engine)

@app.route('/alice-webhook', methods=['POST'])
def handle_alice():
    data = request.json
    user_id = data["session"]["user_id"]
    command = data["request"]["command"].lower()

    # Логика диалога
    if "привет" in command:
        return jsonify({
            "response": {
                "text": "Привет! В каком городе ищем события?",
                "end_session": False
            }
        })
    elif "москва" in command or "питер" in command:
        city = "msk" if "москва" in command else "spb"
        events = get_events(city)
        map_link = generate_map_link(events[:3])  # 3 ближайших события
        return jsonify({
            "response": {
                "text": f"Вот что нашлось в {city}: {events[0]['title']}...",
                "card": {
                    "type": "BigImage",
                    "image_id": map_link
                }
            }
        })

if __name__ == '__main__':
    main()
    app.run(port=5000)