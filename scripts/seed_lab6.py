"""
Сидинг демо-данных для ЛР № 6 (gRPC-микросервис доставки).

Создаёт в БД: роли, admin, курьера, студента с балансом, блюдо меню
и оплаченный заказ. Прямые INSERT/UPDATE в БД — только для подготовки
демо-среды (в живой системе роли назначаются через RBAC-поток).
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Delivery, MenuItem, Order, Role, User  # noqa: E402

PASSWORD = "Passw0rd!"


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        # Роли
        roles = {}
        for name in ("student", "cook", "courier", "admin"):
            role = db.query(Role).filter(Role.name == name).first()
            if not role:
                role = Role(name=name)
                db.add(role)
                db.flush()
            roles[name] = role

        # Пользователи (создаём, если нет; else переиспользуем)
        def get_user(email: str, role_name: str, balance: float = 0.0) -> User:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    phone="+7-999-000-00-00",
                    balance=balance,
                    password_hash=hash_password(PASSWORD),
                    role_id=roles[role_name].id,
                )
                db.add(user)
                db.flush()
            else:
                user.role_id = roles[role_name].id
            return user

        admin = get_user("admin@sirius.ru", "admin")
        courier = get_user("courier@sirius.ru", "courier")
        student = get_user("student@sirius.ru", "student", balance=1000.0)

        # Блюдо меню
        item = db.query(MenuItem).filter(MenuItem.name == "Пицца Маргарита").first()
        if not item:
            item = MenuItem(name="Пицца Маргарита", price=450.0, is_available=True)
            db.add(item)
            db.flush()

        # Оплаченный заказ студента. Демо должно быть повторяемым:
        # сбрасываем прежние активные доставки курьера и старые доставки
        # выбранного заказа, иначе повторный assign упрётся в бизнес-правило
        # «у курьера уже есть активная доставка».
        db.query(Delivery).filter(
            Delivery.courier_id == courier.id,
            Delivery.status == "in_progress",
        ).update({"status": "completed"}, synchronize_session=False)

        order = (
            db.query(Order)
            .filter(Order.user_id == student.id)
            .order_by(Order.id.desc())
            .first()
        )
        if order is None:
            order = Order(user_id=student.id, item_id=item.id, quantity=1, status="paid")
            db.add(order)
            db.flush()
        else:
            order.status = "paid"
            db.query(Delivery).filter(Delivery.order_id == order.id).delete(
                synchronize_session=False
            )

        db.commit()
        print(f"OK: admin id={admin.id}, courier id={courier.id}, "
              f"student id={student.id}, order id={order.id} (status=paid)")


if __name__ == "__main__":
    main()
