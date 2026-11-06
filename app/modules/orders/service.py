"""
Слой бизнес-логики модуля orders (Круги 1 и 2: Entities и Use Cases).

ВАЖНО: в этом файле запрещены импорты fastapi и sqlalchemy.
Сервис зависит только от абстракции репозитория (Protocol, ниже),
а конкретная реализация передаётся в конструктор (инверсия зависимостей).
"""
from typing import Protocol

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError


class OrderRepositoryProtocol(Protocol):
    """Контракт, которого сервис ожидает от слоя хранения данных."""

    def get_user_by_id(self, user_id: int): ...

    def get_menu_item_by_id(self, item_id: int): ...

    def update_user_balance(self, user, new_balance: float) -> None: ...

    def save_order(self, user_id: int, item_id: int, quantity: int) -> int: ...

    def get_order(self, order_id: int): ...

    def set_order_status(self, order, status: str) -> None: ...

    def list_orders_by_status(self, status: str) -> list: ...


class OrderService:
    """
    Класс инкапсулирует бизнес-правила обработки заказов.
    Не имеет зависимостей от инфраструктурных фреймворков.
    """

    def __init__(self, repository: OrderRepositoryProtocol):
        # Внедрение зависимости через конструктор.
        self.repository = repository

    def create_order(self, user_id: int, item_id: int, quantity: int) -> int:
        """
        Исполнение сценария оформления заказа.
        Возвращает идентификатор созданного заказа.
        Возбуждает NotFoundError / BusinessRuleError (наследники ValueError)
        при нарушении бизнес-правил.
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь не найден")

        item = self.repository.get_menu_item_by_id(item_id)
        if not item:
            raise NotFoundError("Блюдо не найдено")

        if not item.is_available:
            raise BusinessRuleError("Блюдо недоступно")

        total_cost = item.price * quantity
        if user.balance < total_cost:
            raise BusinessRuleError("Недостаточно средств на балансе студента")

        # Изменение состояния доменных данных.
        user.balance -= total_cost
        self.repository.update_user_balance(user, user.balance)

        # Делегирование операции сохранения инфраструктурному слою.
        order_id = self.repository.save_order(user_id, item_id, quantity)
        return order_id

    def cancel_order(self, order_id: int, current_user_id: int) -> None:
        """
        Отмена заказа. Закрывает уязвимость IDOR: проверяется, что заказ
        принадлежит именно текущему пользователю (id берётся из JWT,
        а не из запроса). Проверка сознательно находится в Service —
        это бизнес-правило, которое можно протестировать без HTTP
        и переиспользовать в CLI или воркере.

        Возбуждает NotFoundError (404), ForbiddenError (403),
        BusinessRuleError (400).
        """
        order = self.repository.get_order(order_id)
        if not order:
            raise NotFoundError("Заказ не найден")

        # Защита от IDOR: чужой заказ отменять нельзя.
        if order.user_id != current_user_id:
            raise ForbiddenError("Можно отменять только свои заказы")

        if order.status != "processing":
            raise BusinessRuleError("Можно отменить только заказ в обработке")

        self.repository.set_order_status(order, "cancelled")

    def get_kitchen_orders(self) -> list[dict]:
        """
        Очередь заказов для кухни: все заказы в обработке.
        Доступ к сценарию разграничен ролью cook на транспортном слое.
        """
        orders = self.repository.list_orders_by_status("processing")
        return [
            {
                "order_id": order.id,
                "user_id": order.user_id,
                "item_id": order.item_id,
                "quantity": order.quantity,
                "status": order.status,
            }
            for order in orders
        ]
