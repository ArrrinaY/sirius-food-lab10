"""
Транспортный слой модуля orders (Круг 4: Frameworks & Drivers).

Роутер — диспетчер: принимает HTTP-запрос, выполняет техническую
валидацию, собирает слои, вызывает сервис и переводит исключения
в HTTP-статусы. Бизнес-правил и SQL здесь нет.

Все эндпоинты требуют JWT; эндпоинт кухни — роль cook (require_role),
создание заказа — роль student (RBAC: персонал не заказывает еду).
user_id берётся из токена, а не из тела запроса —
так закрыта уязвимость создания заказов от имени других пользователей.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError
from app.database import get_db
from app.models import User
from app.schemas import OrderCreate
from app.modules.orders.repository import OrderRepository
from app.modules.orders.service import OrderService

router = APIRouter()


@router.post("/create")
def create_order(
    payload: OrderCreate,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Заказ может оформить только студент (RBAC): повар, курьер и админ —
    персонал столовой, они еду через этот API не заказывают.
    Проверка роли — на транспортном слое (свойство точки входа).
    """
    # Техническая валидация уровня транспортного протокола.
    if payload.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Количество должно быть больше нуля",
        )

    # Сборка архитектурных слоёв.
    repository = OrderRepository(db)
    service = OrderService(repository)

    # user_id берётся из JWT, а не из payload — клиент не может
    # создать заказ от имени другого пользователя.
    try:
        order_id = service.create_order(
            user_id=current_user.id,
            item_id=payload.item_id,
            quantity=payload.quantity,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "order_id": order_id}


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Отмена заказа. Проверка «заказ принадлежит текущему пользователю»
    (защита от IDOR) выполняется в Service-слое.
    """
    repository = OrderRepository(db)
    service = OrderService(repository)

    try:
        service.cancel_order(order_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success"}


@router.get("/kitchen/orders")
def kitchen_orders(
    current_user: User = Depends(require_role("cook")),
    db: Session = Depends(get_db),
):
    """Очередь заказов для кухни. Только для роли cook (RBAC)."""
    service = OrderService(OrderRepository(db))
    return service.get_kitchen_orders()
