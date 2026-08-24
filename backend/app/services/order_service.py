"""Order service — atomic order creation and charge storage."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrderNotFoundError
from app.models.notification import NotificationEvent
from app.models.order import Order, OrderStatus
from app.models.order_address import AddressType, OrderAddress
from app.models.order_package import OrderPackage
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderCreateRequest
from app.services.rate_calculation_service import RateCalculationService
from app.services.notification_service import NotificationService


class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.rate_service = RateCalculationService(db)
        self.notif_service = NotificationService(db)

    async def calculate_rate(self, data: "OrderCreateRequest | RateCalcRequest", order_type, payment_type) -> "RateCalculationResult":  # noqa
        from app.services.rate_calculation_service import RateCalculationService
        svc = RateCalculationService(self.db)
        return await svc.calculate(
            pickup_postal_code=data.pickup_address.postal_code,
            drop_postal_code=data.drop_address.postal_code,
            length_cm=data.package.length_cm,
            breadth_cm=data.package.breadth_cm,
            height_cm=data.package.height_cm,
            actual_weight_kg=data.package.actual_weight_kg,
            order_type=order_type,
            payment_type=payment_type,
        )

    async def create_order(
        self,
        data: "OrderCreateRequest",
        current_user: User,
        customer_id: UUID | None = None,
    ) -> Order:
        """
        Atomically creates an order with:
        - rate calculation
        - order record
        - pickup + drop addresses
        - package record
        - initial status history
        All within a single transaction.
        """
        # Determine customer
        effective_customer_id = customer_id or current_user.id

        # Rate calculation (recalculated server-side for integrity)
        calc = await self.rate_service.calculate(
            pickup_postal_code=data.pickup_address.postal_code,
            drop_postal_code=data.drop_address.postal_code,
            length_cm=data.package.length_cm,
            breadth_cm=data.package.breadth_cm,
            height_cm=data.package.height_cm,
            actual_weight_kg=data.package.actual_weight_kg,
            order_type=data.order_type,
            payment_type=data.payment_type,
        )

        # Generate order number
        order_number = await self.order_repo.generate_order_number()

        # Create order
        from uuid import UUID as UUID_type
        order = await self.order_repo.create(
            order_number=order_number,
            customer_id=effective_customer_id,
            pickup_zone_id=UUID_type(calc.pickup_zone_id),
            drop_zone_id=UUID_type(calc.drop_zone_id),
            order_type=data.order_type,
            payment_type=data.payment_type,
            zone_type=calc.zone_type,
            actual_weight=calc.actual_weight,
            volumetric_weight=calc.volumetric_weight,
            billable_weight=calc.billable_weight,
            base_charge=calc.base_charge,
            cod_charge=calc.cod_surcharge,
            total_charge=calc.total_charge,
            status=OrderStatus.CREATED,
            created_by=current_user.id,
            confirmed_at=datetime.now(UTC),
        )

        # Pickup address
        pa = data.pickup_address
        self.db.add(OrderAddress(
            order_id=order.id,
            address_type=AddressType.PICKUP,
            name=pa.name,
            phone=pa.phone,
            address_line1=pa.address_line1,
            address_line2=pa.address_line2,
            city=pa.city,
            state=pa.state,
            postal_code=pa.postal_code,
            country=pa.country or "India",
        ))

        # Drop address
        da = data.drop_address
        self.db.add(OrderAddress(
            order_id=order.id,
            address_type=AddressType.DROP,
            name=da.name,
            phone=da.phone,
            address_line1=da.address_line1,
            address_line2=da.address_line2,
            city=da.city,
            state=da.state,
            postal_code=da.postal_code,
            country=da.country or "India",
        ))

        # Package
        pkg = data.package
        self.db.add(OrderPackage(
            order_id=order.id,
            length_cm=pkg.length_cm,
            breadth_cm=pkg.breadth_cm,
            height_cm=pkg.height_cm,
            actual_weight_kg=pkg.actual_weight_kg,
        ))

        # Initial status history
        self.db.add(OrderStatusHistory(
            order_id=order.id,
            previous_status=None,
            new_status=OrderStatus.CREATED,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            remarks="Order created",
        ))

        # Initial delivery attempt
        from app.models.delivery_attempt import AttemptOutcome, DeliveryAttempt
        self.db.add(DeliveryAttempt(
            order_id=order.id,
            attempt_number=1,
            outcome=AttemptOutcome.PENDING,
        ))

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(order)

        # Notify (non-fatal if fails)
        try:
            from app.repositories.user_repo import UserRepository
            customer = await UserRepository(self.db).get(effective_customer_id)
            if customer:
                await self.notif_service.notify_order_event(
                    NotificationEvent.ORDER_CREATED, order, customer
                )
                await self.db.commit()
        except Exception:
            pass

        # Reload with all relationships so Pydantic can serialize it
        return await self.get_order(order.id)

    async def get_order_for_customer(self, order_id: UUID, customer_id: UUID) -> Order:
        order = await self.order_repo.get_with_relations(order_id)
        if order is None or order.customer_id != customer_id:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        return order

    async def get_order(self, order_id: UUID) -> Order:
        order = await self.order_repo.get_with_relations(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        return order
