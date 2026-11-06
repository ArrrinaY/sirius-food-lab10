"""
Транспортный слой модуля delivery (Круг 4: Frameworks & Drivers).

Назначение курьера — роль admin, завершение и просмотр доставок — роль
courier (RBAC на транспортном слое). Проверка прав на конкретный объект
(защита от IDOR) — в Service-слое.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.exceptions import ForbiddenError, NotFoundError
from app.database import get_db
from app.models import User
from app.schemas import DeliveryAssign
from app.modules.delivery.repository import DeliveryRepository
from app.modules.delivery.service import DeliveryService

router = APIRouter()


@router.post("/assign")
def assign_courier(
    payload: DeliveryAssign,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Назначение курьера на заказ. Только для роли admin (RBAC)."""
    service = DeliveryService(DeliveryRepository(db))

    try:
        delivery_id = service.assign_courier(
            order_id=payload.order_id, courier_id=payload.courier_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "delivery_id": delivery_id}


@router.patch("/{delivery_id}/complete")
def complete_delivery(
    delivery_id: int,
    current_user: User = Depends(require_role("courier")),
    db: Session = Depends(get_db),
):
    """Завершение доставки. Только для роли courier (RBAC)."""
    service = DeliveryService(DeliveryRepository(db))

    try:
        # Проверка «доставка принадлежит этому курьеру» (IDOR) — в Service.
        service.complete_delivery(delivery_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success"}


@router.get("/my")
def my_deliveries(
    current_user: User = Depends(require_role("courier")),
    db: Session = Depends(get_db),
):
    """Доставки текущего курьера. Чужие доставки не видны (IDOR)."""
    service = DeliveryService(DeliveryRepository(db))
    return service.my_deliveries(current_user.id)
