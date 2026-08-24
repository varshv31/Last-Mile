"""Initial database schema — all tables.

Revision ID: 0001
Revises: 
Create Date: 2026-08-22

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("role", sa.Enum("CUSTOMER", "AGENT", "ADMIN", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    # ── zones ──────────────────────────────────────────────────
    op.create_table(
        "zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_zones_code", "zones", ["code"])

    # ── areas ──────────────────────────────────────────────────
    op.create_table(
        "areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("postal_code"),
    )
    op.create_index("ix_areas_postal_code", "areas", ["postal_code"])
    op.create_index("ix_areas_zone_id", "areas", ["zone_id"])

    # ── rate_cards ─────────────────────────────────────────────
    op.create_table(
        "rate_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_type", sa.Enum("B2B", "B2C", name="ordertype"), nullable=False),
        sa.Column("zone_type", sa.Enum("INTRA_ZONE", "INTER_ZONE", name="zonetype"), nullable=False),
        sa.Column("min_weight", sa.Float(), nullable=False),
        sa.Column("max_weight", sa.Float(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rate_cards_order_type", "rate_cards", ["order_type"])
    op.create_index("ix_rate_cards_zone_type", "rate_cards", ["zone_type"])

    # ── cod_surcharges ─────────────────────────────────────────
    op.create_table(
        "cod_surcharges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_type", sa.Enum("B2B", "B2C", name="ordertype"), nullable=False),
        sa.Column("surcharge_type", sa.Enum("FIXED", "PERCENTAGE", name="surchargetype"), nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_type"),
    )

    # ── orders ─────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.String(30), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pickup_zone_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("drop_zone_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_type", sa.Enum("B2B", "B2C", name="ordertype"), nullable=False),
        sa.Column("payment_type", sa.Enum("PREPAID", "COD", name="paymenttype"), nullable=False),
        sa.Column("zone_type", sa.Enum("INTRA_ZONE", "INTER_ZONE", name="zonetype"), nullable=True),
        sa.Column("actual_weight", sa.Numeric(10, 3), nullable=False),
        sa.Column("volumetric_weight", sa.Numeric(10, 3), nullable=False),
        sa.Column("billable_weight", sa.Numeric(10, 3), nullable=False),
        sa.Column("base_charge", sa.Numeric(10, 2), nullable=False),
        sa.Column("cod_charge", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_charge", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.Enum("CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY",
                                     "DELIVERED", "FAILED", "CANCELLED", name="orderstatus"), nullable=False),
        sa.Column("assigned_agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["pickup_zone_id"], ["zones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["drop_zone_id"], ["zones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_agent_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    for col in ["order_number", "status", "customer_id", "assigned_agent_id",
                "pickup_zone_id", "drop_zone_id", "created_at"]:
        op.create_index(f"ix_orders_{col}", "orders", [col])

    # ── order_addresses ────────────────────────────────────────
    op.create_table(
        "order_addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_type", sa.Enum("PICKUP", "DROP", name="addresstype"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address_line1", sa.String(500), nullable=False),
        sa.Column("address_line2", sa.String(500), nullable=True),
        sa.Column("city", sa.String(255), nullable=False),
        sa.Column("state", sa.String(255), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── order_packages ─────────────────────────────────────────
    op.create_table(
        "order_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("length_cm", sa.Numeric(10, 2), nullable=False),
        sa.Column("breadth_cm", sa.Numeric(10, 2), nullable=False),
        sa.Column("height_cm", sa.Numeric(10, 2), nullable=False),
        sa.Column("actual_weight_kg", sa.Numeric(10, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )

    # ── order_status_history ───────────────────────────────────
    op.create_table(
        "order_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_status", sa.Enum("CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY",
                                              "DELIVERED", "FAILED", "CANCELLED", name="orderstatus"), nullable=True),
        sa.Column("new_status", sa.Enum("CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY",
                                         "DELIVERED", "FAILED", "CANCELLED", name="orderstatus"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_role", sa.Enum("CUSTOMER", "AGENT", "ADMIN", name="userrole"), nullable=True),
        sa.Column("remarks", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_status_history_order_id", "order_status_history", ["order_id"])

    # ── delivery_agents ────────────────────────────────────────
    op.create_table(
        "delivery_agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("current_longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("current_zone_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("availability_status", sa.Enum("AVAILABLE", "BUSY", "OFFLINE", name="availabilitystatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["current_zone_id"], ["zones.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_delivery_agents_availability_status", "delivery_agents", ["availability_status"])
    op.create_index("ix_delivery_agents_current_zone_id", "delivery_agents", ["current_zone_id"])

    # ── agent_assignments ──────────────────────────────────────
    op.create_table(
        "agent_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assignment_type", sa.Enum("MANUAL", "AUTO", name="assignmenttype"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["delivery_agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_assignments_order_id", "agent_assignments", ["order_id"])
    op.create_index("ix_agent_assignments_agent_id", "agent_assignments", ["agent_id"])

    # ── delivery_attempts ──────────────────────────────────────
    op.create_table(
        "delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("assigned_agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.Enum("PENDING", "DELIVERED", "FAILED", name="attemptoutcome"), nullable=False),
        sa.Column("failure_reason", sa.Enum("CUSTOMER_NOT_AVAILABLE", "WRONG_ADDRESS", "CUSTOMER_REJECTED",
                                             "ACCESS_ISSUE", "OTHER", name="failurereason"), nullable=True),
        sa.Column("remarks", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_agent_id"], ["delivery_agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_delivery_attempts_order_id", "delivery_attempts", ["order_id"])

    # ── reschedule_requests ────────────────────────────────────
    op.create_table(
        "reschedule_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", name="reschedulestatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["previous_attempt_id"], ["delivery_attempts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── notifications ──────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.Enum("EMAIL", "SMS", name="notificationchannel"), nullable=False),
        sa.Column("event_type", sa.Enum("ORDER_CREATED", "ORDER_PICKED_UP", "ORDER_IN_TRANSIT",
                                         "ORDER_OUT_FOR_DELIVERY", "ORDER_DELIVERED", "ORDER_FAILED",
                                         "ORDER_CANCELLED", "ORDER_RESCHEDULED", name="notificationevent"), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "SENT", "FAILED", name="notificationstatus"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_order_id", "notifications", ["order_id"])
    op.create_index("ix_notifications_status", "notifications", ["status"])

    # ── audit_logs ─────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("old_value", postgresql.JSON(), nullable=True),
        sa.Column("new_value", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_entity_type_id", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    for table in [
        "audit_logs", "notifications", "reschedule_requests",
        "delivery_attempts", "agent_assignments", "delivery_agents",
        "order_status_history", "order_packages", "order_addresses",
        "orders", "cod_surcharges", "rate_cards", "areas", "zones", "users",
    ]:
        op.drop_table(table)
    for enum in [
        "userrole", "ordertype", "zonetype", "surchargetype", "paymenttype",
        "orderstatus", "addresstype", "availabilitystatus", "assignmenttype",
        "attemptoutcome", "failurereason", "reschedulestatus",
        "notificationchannel", "notificationevent", "notificationstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
