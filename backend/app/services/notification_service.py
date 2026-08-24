"""Notification service — email/SMS abstraction with BackgroundTasks dispatch.

Design principles:
- Provider failures NEVER roll back order transactions.
- Notifications are dispatched via FastAPI BackgroundTasks.
- Provider implementations are swappable via environment config.
- All notification outcomes are logged to the notifications table.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationEvent,
    NotificationStatus,
)
from app.models.order import Order
from app.models.user import User
from app.repositories.notification_repo import NotificationRepository

logger = logging.getLogger(__name__)


# ── Provider implementations ──────────────────────────────────────────────────

async def _send_email(recipient: str, subject: str, body: str) -> str | None:
    """Send an email. Returns provider message ID or None on failure."""
    if settings.EMAIL_DISABLED or not settings.SMTP_USERNAME:
        logger.info("[EMAIL-NOOP] To: %s | Subject: %s", recipient, subject)
        return "noop"
    try:
        import aiosmtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = recipient
        msg["Subject"] = subject

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        return f"smtp-{datetime.now(UTC).timestamp()}"
    except Exception as e:
        logger.error("[EMAIL-FAIL] %s: %s", recipient, e)
        raise


async def _send_sms(phone: str, body: str) -> str | None:
    """Send an SMS via Twilio. Returns message SID or None on failure."""
    if settings.SMS_DISABLED or not settings.TWILIO_ACCOUNT_SID:
        logger.info("[SMS-NOOP] To: %s | %s", phone, body[:60])
        return "noop"
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone,
        )
        return message.sid
    except Exception as e:
        logger.error("[SMS-FAIL] %s: %s", phone, e)
        raise


# ── Message templates ─────────────────────────────────────────────────────────

_TEMPLATES: dict[NotificationEvent, tuple[str, str]] = {
    NotificationEvent.ORDER_CREATED: (
        "Your order has been placed",
        "Your order {order_number} has been created. Total charge: ₹{total_charge}.",
    ),
    NotificationEvent.ORDER_PICKED_UP: (
        "Your order has been picked up",
        "Your order {order_number} has been picked up by our agent.",
    ),
    NotificationEvent.ORDER_IN_TRANSIT: (
        "Your order is in transit",
        "Your order {order_number} is now in transit.",
    ),
    NotificationEvent.ORDER_OUT_FOR_DELIVERY: (
        "Out for delivery",
        "Your order {order_number} is out for delivery. Expect it today!",
    ),
    NotificationEvent.ORDER_DELIVERED: (
        "Order delivered",
        "Your order {order_number} has been successfully delivered. Thank you!",
    ),
    NotificationEvent.ORDER_FAILED: (
        "Delivery attempt failed",
        "We were unable to deliver your order {order_number}. You can reschedule via the app.",
    ),
    NotificationEvent.ORDER_CANCELLED: (
        "Order cancelled",
        "Your order {order_number} has been cancelled.",
    ),
    NotificationEvent.ORDER_RESCHEDULED: (
        "Delivery rescheduled",
        "Your order {order_number} has been rescheduled for a new delivery attempt.",
    ),
}


def _build_message(event: NotificationEvent, order: Order) -> tuple[str, str]:
    subject_tmpl, body_tmpl = _TEMPLATES.get(
        event,
        ("Order update", "Your order {order_number} has been updated."),
    )
    ctx = {
        "order_number": order.order_number,
        "total_charge": order.total_charge,
    }
    return subject_tmpl, body_tmpl.format(**ctx)


# ── Notification service ──────────────────────────────────────────────────────

class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = NotificationRepository(db)
        self.db = db

    async def _record_and_send(
        self,
        *,
        user: User,
        order: Order | None,
        channel: NotificationChannel,
        event: NotificationEvent,
        recipient: str,
        subject: str | None,
        message: str,
    ) -> None:
        """Persist a notification row, attempt delivery, update status."""
        notif = await self.repo.create(
            user_id=user.id,
            order_id=order.id if order else None,
            channel=channel,
            event_type=event,
            recipient=recipient,
            subject=subject,
            message=message,
            status=NotificationStatus.PENDING,
        )
        try:
            if channel == NotificationChannel.EMAIL:
                msg_id = await _send_email(recipient, subject or "Order Update", message)
            else:
                msg_id = await _send_sms(recipient, message)

            notif.status = NotificationStatus.SENT
            notif.provider_message_id = msg_id
            notif.sent_at = datetime.now(UTC)
        except Exception as exc:
            notif.status = NotificationStatus.FAILED
            notif.error_message = str(exc)[:500]
            logger.warning("Notification failed (non-fatal): %s", exc)

        self.db.add(notif)
        # NOTE: We flush but do NOT commit here.
        # The calling order service owns the transaction.
        await self.db.flush()

    async def notify_order_event(self, event: NotificationEvent, order: Order, user: User) -> None:
        """Dispatch EMAIL + SMS notifications for an order event."""
        subject, message = _build_message(event, order)

        # Email
        if user.email:
            await self._record_and_send(
                user=user,
                order=order,
                channel=NotificationChannel.EMAIL,
                event=event,
                recipient=user.email,
                subject=subject,
                message=message,
            )

        # SMS
        if user.phone:
            await self._record_and_send(
                user=user,
                order=order,
                channel=NotificationChannel.SMS,
                event=event,
                recipient=user.phone,
                subject=None,
                message=message,
            )
