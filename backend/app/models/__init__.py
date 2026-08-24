"""SQLAlchemy models package — imports ensure all models are registered."""
from app.models.user import User, UserRole
from app.models.zone import Zone
from app.models.area import Area
from app.models.rate_card import RateCard, OrderType, ZoneType
from app.models.cod_surcharge import CODSurcharge, SurchargeType
from app.models.order import Order, OrderStatus, PaymentType
from app.models.order_address import OrderAddress, AddressType
from app.models.order_package import OrderPackage
from app.models.order_status_history import OrderStatusHistory
from app.models.delivery_agent import DeliveryAgent, AvailabilityStatus
from app.models.agent_assignment import AgentAssignment, AssignmentType
from app.models.delivery_attempt import DeliveryAttempt, AttemptOutcome, FailureReason
from app.models.reschedule_request import RescheduleRequest, RescheduleStatus
from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationEvent
from app.models.audit_log import AuditLog

__all__ = [
    "User", "UserRole",
    "Zone",
    "Area",
    "RateCard", "OrderType", "ZoneType",
    "CODSurcharge", "SurchargeType",
    "Order", "OrderStatus", "PaymentType",
    "OrderAddress", "AddressType",
    "OrderPackage",
    "OrderStatusHistory",
    "DeliveryAgent", "AvailabilityStatus",
    "AgentAssignment", "AssignmentType",
    "DeliveryAttempt", "AttemptOutcome", "FailureReason",
    "RescheduleRequest", "RescheduleStatus",
    "Notification", "NotificationChannel", "NotificationStatus", "NotificationEvent",
    "AuditLog",
]
