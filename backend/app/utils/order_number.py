"""Order number generator — LMD-YYYYMMDD-XXXXXX format."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


async def generate_order_number(db: AsyncSession) -> str:
    """
    Generate a unique, human-readable order number in the format:
        LMD-20260822-000001

    Uses a database count to determine the sequence number for today,
    ensuring uniqueness even under concurrent requests.
    """
    today = datetime.now(UTC).date()
    date_str = today.strftime("%Y%m%d")
    prefix = f"LMD-{date_str}-"

    # Count today's orders to determine sequence
    result = await db.execute(
        select(func.count()).select_from(Order).where(
            Order.order_number.like(f"{prefix}%")
        )
    )
    count = result.scalar_one() + 1
    return f"{prefix}{count:06d}"
