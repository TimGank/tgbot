from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Подключение к SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./events.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# База для моделей
Base = declarative_base()

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()