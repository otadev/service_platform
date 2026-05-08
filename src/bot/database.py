import os
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

#подключение к базе данных
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL) #соединение с БД
Session = sessionmaker(bind=engine) #фабрика сессий
Base = declarative_base() #базовый класс для моделей

class CustomUser(Base):
    __tablename__ = 'users_customuser'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    phone = Column(String)
    telegram_id = Column(BigInteger, nullable=True)

def get_user_by_phone(phone: str): #пользователь вводит телефон, мы ищем его в БД
    session = Session()
    try:
        return session.query(CustomUser).filter(CustomUser.phone ==phone).first()
    finally:
        session.close()

def save_telegram_id(user_id: int, telegram_id: int): #нашли пользователя, сохраняем его Telegram ID
    session = Session()
    try:
        user = session.query(CustomUser).filter(CustomUser.id == user_id).first()
        if user:
            user.telegram_id = telegram_id
            session.commit()
            return True
        return False
    finally:
        session.close()

