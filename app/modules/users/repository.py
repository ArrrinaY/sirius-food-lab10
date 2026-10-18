"""
Инфраструктурный слой модуля users (Круг 3: Interface Adapters).

Единственный файл модуля, который знает о SQLAlchemy и структуре таблиц.
"""
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """Операции ввода-вывода для пользователей. Бизнес-правил не содержит."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int):
        """Извлечение пользователя по идентификатору."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str):
        """Извлечение пользователя по email (для проверки уникальности)."""
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, email: str, phone):
        """Создание пользователя с нулевым балансом. Возвращает (id, email)."""
        new_user = User(
            email=email,
            phone=phone,
            balance=0.0,
            is_blocked=False,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user.id, new_user.email

    def update_user_balance(self, user, new_balance: float) -> float:
        """Сохранение нового баланса. Возвращает баланс после записи."""
        user.balance = new_balance
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user.balance
