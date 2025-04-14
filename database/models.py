from sqlalchemy import Column, Integer, String, JSON
from database.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)  # user_id из Алисы
    city = Column(String)                 # Сохранённый город
    preferences = Column(JSON)            # Любимые категории событий

class DialogState(Base):
    __tablename__ = "dialogs"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    step = Column(String)  # Текущий шаг диалога ("выбор города", "выбор категории")
    context = Column(JSON)  # Доп. данные (например, выбранные события)