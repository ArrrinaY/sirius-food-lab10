"""
Unit-тесты UserService. СУБД не требуется (in-memory заглушка репозитория).
"""
import unittest
from types import SimpleNamespace

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.modules.users.service import UserService


class FakeUserRepository:
    def __init__(self, users=None):
        self.users = {u.id: u for u in (users or [])}
        self.next_id = 100

    def get_user_by_id(self, user_id):
        return self.users.get(user_id)

    def get_user_by_email(self, email):
        return next((u for u in self.users.values() if u.email == email), None)

    def create_user(self, email, phone):
        user = SimpleNamespace(
            id=self.next_id, email=email, phone=phone,
            balance=0.0, is_blocked=False,
        )
        self.users[user.id] = user
        self.next_id += 1
        return user.id, user.email

    def update_user_balance(self, user, new_balance):
        user.balance = new_balance
        return user.balance


def make_user(**kw):
    data = dict(id=1, email="a@b.ru", phone=None, balance=100.0, is_blocked=False)
    data.update(kw)
    return SimpleNamespace(**data)


class RegisterTests(unittest.TestCase):
    def test_register_success(self):
        repo = FakeUserRepository()
        result = UserService(repo).register_user("new@mail.ru", "+79991234567")
        self.assertEqual(result.email, "new@mail.ru")
        self.assertEqual(repo.users[result.id].balance, 0.0)

    def test_register_without_phone(self):
        result = UserService(FakeUserRepository()).register_user("x@y.ru", None)
        self.assertIsNotNone(result.id)

    def test_duplicate_email(self):
        service = UserService(FakeUserRepository([make_user(email="dup@mail.ru")]))
        with self.assertRaises(BusinessRuleError) as ctx:
            service.register_user("dup@mail.ru", None)
        self.assertEqual(
            str(ctx.exception), "Пользователь с таким email уже зарегистрирован"
        )

    def test_short_phone(self):
        repo = FakeUserRepository()
        with self.assertRaises(BusinessRuleError) as ctx:
            UserService(repo).register_user("p@mail.ru", "12345")
        self.assertEqual(str(ctx.exception), "Некорректный формат номера телефона")
        self.assertEqual(repo.users, {})


class TopUpTests(unittest.TestCase):
    def test_topup_success(self):
        repo = FakeUserRepository([make_user(balance=100)])
        self.assertEqual(UserService(repo).top_up_balance(1, 250.5), 350.5)

    def test_user_not_found(self):
        with self.assertRaises(NotFoundError):
            UserService(FakeUserRepository()).top_up_balance(1, 10)

    def test_blocked_user(self):
        repo = FakeUserRepository([make_user(is_blocked=True)])
        with self.assertRaises(ForbiddenError) as ctx:
            UserService(repo).top_up_balance(1, 10)
        self.assertEqual(
            str(ctx.exception), "Пользователь заблокирован. Пополнение невозможно"
        )
        self.assertEqual(repo.users[1].balance, 100)

    def test_limit_exceeded(self):
        repo = FakeUserRepository([make_user()])
        with self.assertRaises(BusinessRuleError):
            UserService(repo).top_up_balance(1, 50000.01)
        self.assertEqual(repo.users[1].balance, 100)

    def test_limit_boundary_allowed(self):
        repo = FakeUserRepository([make_user(balance=0)])
        self.assertEqual(UserService(repo).top_up_balance(1, 50000), 50000)

    def test_not_found_checked_before_blocked_and_limit(self):
        """Порядок проверок как в MVP: 404 -> 403 -> лимит."""
        repo = FakeUserRepository([make_user(is_blocked=True)])
        with self.assertRaises(ForbiddenError):
            UserService(repo).top_up_balance(1, 10**6)


if __name__ == "__main__":
    unittest.main()
