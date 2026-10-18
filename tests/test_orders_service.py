"""
Unit-тесты OrderService. Не требуют СУБД, FastAPI и SQLAlchemy:
вместо настоящего репозитория используется in-memory заглушка.
Запуск: python -m unittest discover -s tests -v   (или pytest)
"""
import unittest
from types import SimpleNamespace

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.modules.orders.service import OrderService


class FakeOrderRepository:
    """Заглушка репозитория заказов, хранящая данные в памяти."""

    def __init__(self, users=None, items=None):
        self.users = {u.id: u for u in (users or [])}
        self.items = {i.id: i for i in (items or [])}
        self.saved_orders = []
        self.balance_updates = []

    def get_user_by_id(self, user_id):
        return self.users.get(user_id)

    def get_menu_item_by_id(self, item_id):
        return self.items.get(item_id)

    def update_user_balance(self, user, new_balance):
        self.balance_updates.append((user.id, new_balance))
        user.balance = new_balance

    def save_order(self, user_id, item_id, quantity):
        self.saved_orders.append((user_id, item_id, quantity))
        return len(self.saved_orders)


def make_service(balance=500.0, price=100.0, available=True):
    user = SimpleNamespace(id=1, balance=balance)
    item = SimpleNamespace(id=10, price=price, is_available=available)
    repo = FakeOrderRepository([user], [item])
    return OrderService(repo), repo, user


class OrderServiceTests(unittest.TestCase):
    def test_success_debits_balance_and_saves_order(self):
        service, repo, user = make_service(balance=500, price=100)
        order_id = service.create_order(user_id=1, item_id=10, quantity=3)
        self.assertEqual(order_id, 1)
        self.assertEqual(user.balance, 200)
        self.assertEqual(repo.balance_updates, [(1, 200)])
        self.assertEqual(repo.saved_orders, [(1, 10, 3)])

    def test_user_not_found(self):
        service, repo, _ = make_service()
        with self.assertRaises(NotFoundError) as ctx:
            service.create_order(user_id=999, item_id=10, quantity=1)
        self.assertEqual(str(ctx.exception), "Пользователь не найден")
        self.assertEqual(repo.saved_orders, [])

    def test_item_not_found(self):
        service, repo, _ = make_service()
        with self.assertRaises(NotFoundError) as ctx:
            service.create_order(user_id=1, item_id=999, quantity=1)
        self.assertEqual(str(ctx.exception), "Блюдо не найдено")
        self.assertEqual(repo.saved_orders, [])

    def test_item_unavailable(self):
        service, repo, _ = make_service(available=False)
        with self.assertRaises(BusinessRuleError) as ctx:
            service.create_order(user_id=1, item_id=10, quantity=1)
        self.assertEqual(str(ctx.exception), "Блюдо недоступно")
        self.assertEqual(repo.saved_orders, [])

    def test_insufficient_funds_does_not_change_state(self):
        service, repo, user = make_service(balance=50, price=100)
        with self.assertRaises(BusinessRuleError) as ctx:
            service.create_order(user_id=1, item_id=10, quantity=1)
        self.assertEqual(
            str(ctx.exception), "Недостаточно средств на балансе студента"
        )
        self.assertEqual(user.balance, 50)
        self.assertEqual(repo.balance_updates, [])
        self.assertEqual(repo.saved_orders, [])

    def test_exact_balance_is_enough(self):
        service, _, user = make_service(balance=300, price=100)
        service.create_order(user_id=1, item_id=10, quantity=3)
        self.assertEqual(user.balance, 0)

    def test_errors_are_value_errors(self):
        """Совместимость с шаблоном методички: except ValueError."""
        service, _, _ = make_service()
        with self.assertRaises(ValueError):
            service.create_order(user_id=999, item_id=10, quantity=1)


if __name__ == "__main__":
    unittest.main()
