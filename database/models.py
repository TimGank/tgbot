from database.session import Base
from sqlalchemy import Column, String, Integer, JSON

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    city = Column(String)
    preferences = Column(JSON)

class DialogState(Base):
    __tablename__ = "dialogs"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    step = Column(String)
    context = Column(JSON)