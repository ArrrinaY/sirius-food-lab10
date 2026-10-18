"""
Модуль инициализации подключения к СУБД PostgreSQL.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sirius:sirius@localhost:5432/sirius_food",
)

# SQL_ECHO=true (по умолчанию) выводит SQL-запросы в терминал —
# нужно для проверки INSERT/UPDATE при выполнении лабораторной работы.
SQL_ECHO = os.getenv("SQL_ECHO", "true").lower() in ("1", "true", "yes")

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Генератор сессии базы данных для использования в Depends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
