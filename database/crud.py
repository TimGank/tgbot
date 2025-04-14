from sqlalchemy.orm import Session
from database.session import SessionLocal
from database.models import User

def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def update_user_city(db: Session, user_id: str, city: str):
    user = get_user(db, user_id)
    if not user:
        user = User(id=user_id, city=city)
        db.add(user)
    else:
        user.city = city
    db.commit()