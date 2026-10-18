"""
Слой бизнес-логики модуля users (Круги 1 и 2: Entities и Use Cases).

ВАЖНО: в этом файле запрещены импорты fastapi и sqlalchemy.
Репозиторий передаётся в конструктор (инверсия зависимостей).
"""
from dataclasses import dataclass
from typing import Optional, Protocol

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError

MAX_TOPUP_AMOUNT = 50000
MIN_PHONE_LENGTH = 10


@dataclass(frozen=True)
class RegisteredUser:
    """Результат сценария регистрации (без привязки к ORM)."""

    id: int
    email: str


class UserRepositoryProtocol(Protocol):
    """Контракт, которого сервис ожидает от слоя хранения данных."""

    def get_user_by_id(self, user_id: int): ...

    def get_user_by_email(self, email: str): ...

    def create_user(self, email: str, phone: Optional[str]): ...

    def update_user_balance(self, user, new_balance: float) -> float: ...


class UserService:
    """Бизнес-правила работы с пользователями."""

    def __init__(self, repository: UserRepositoryProtocol):
        # Внедрение зависимости через конструктор.
        self.repository = repository

    def register_user(self, email: str, phone: Optional[str]) -> RegisteredUser:
        """
        Регистрация нового пользователя.
        Формат email уже проверен Pydantic (EmailStr) в транспортном слое;
        здесь проверяется только уникальность — это бизнес-правило.
        """
        if self.repository.get_user_by_email(email):
            raise BusinessRuleError(
                "Пользователь с таким email уже зарегистрирован"
            )

        # Порядок проверок сохранён как в MVP: сначала уникальность email.
        if phone and len(phone) < MIN_PHONE_LENGTH:
            raise BusinessRuleError("Некорректный формат номера телефона")

        user_id, user_email = self.repository.create_user(email, phone)
        return RegisteredUser(id=user_id, email=user_email)

    def top_up_balance(self, user_id: int, amount: float) -> float:
        """
        Пополнение баланса. Возвращает новый баланс.
        Положительность суммы проверяется в router (техническая валидация).
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь не найден")

        if user.is_blocked:
            raise ForbiddenError("Пользователь заблокирован. Пополнение невозможно")

        if amount > MAX_TOPUP_AMOUNT:
            raise BusinessRuleError("Максимальная сумма пополнения — 50000 рублей")

        return self.repository.update_user_balance(user, user.balance + amount)
