"""Order schemas — request/response for order creation and rate calculation."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.order import OrderStatus, PaymentType
from app.models.rate_card import OrderType, ZoneType


class AddressInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., max_length=20)
    address_line1: str = Field(..., min_length=1, max_length=500)
    address_line2: str | None = None
    city: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=1, max_length=255)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str | None = "India"


class PackageInput(BaseModel):
    length_cm: float = Field(..., gt=0, description="Length in centimetres")
    breadth_cm: float = Field(..., gt=0, description="Breadth in centimetres")
    height_cm: float = Field(..., gt=0, description="Height in centimetres")
    actual_weight_kg: float = Field(..., gt=0, description="Actual weight in kilograms")


class RateCalculateRequest(BaseModel):
    pickup_address: AddressInput
    drop_address: AddressInput
    package: PackageInput
    order_type: OrderType
    payment_type: PaymentType

    model_config = {"json_schema_extra": {"example": {
        "pickup_address": {
            "name": "Sender Name", "phone": "9876543210",
            "address_line1": "123 MG Road", "city": "Mumbai", "state": "Maharashtra",
            "postal_code": "400069",
        },
        "drop_address": {
            "name": "Receiver Name", "phone": "9123456789",
            "address_line1": "45 Anna Nagar", "city": "Chennai", "state": "Tamil Nadu",
            "postal_code": "600040",
        },
        "package": {"length_cm": 20, "breadth_cm": 15, "height_cm": 10, "actual_weight_kg": 1.5},
        "order_type": "B2C",
        "payment_type": "COD",
    }}}


class RateCalculateResponse(BaseModel):
    pickup_area_name: str
    pickup_postal_code: str
    pickup_zone_id: str
    pickup_zone_name: str
    drop_area_name: str
    drop_postal_code: str
    drop_zone_id: str
    drop_zone_name: str
    zone_type: ZoneType
    actual_weight: float
    volumetric_weight: float
    billable_weight: float
    rate_card_id: str
    base_charge: float
    cod_surcharge: float
    total_charge: float
    order_type: OrderType
    payment_type: PaymentType


class OrderCreateRequest(BaseModel):
    pickup_address: AddressInput
    drop_address: AddressInput
    package: PackageInput
    order_type: OrderType
    payment_type: PaymentType

    model_config = {"json_schema_extra": {"example": {
        "pickup_address": {
            "name": "Sender", "phone": "9876543210",
            "address_line1": "10 Linking Road", "city": "Mumbai", "state": "Maharashtra",
            "postal_code": "400069",
        },
        "drop_address": {
            "name": "Receiver", "phone": "9000000001",
            "address_line1": "5 T Nagar", "city": "Chennai", "state": "Tamil Nadu",
            "postal_code": "600040",
        },
        "package": {"length_cm": 30, "breadth_cm": 20, "height_cm": 15, "actual_weight_kg": 2.0},
        "order_type": "B2C",
        "payment_type": "PREPAID",
    }}}


class AdminOrderCreateRequest(OrderCreateRequest):
    customer_id: uuid.UUID = Field(..., description="Customer UUID on whose behalf the order is created")


class AddressResponse(BaseModel):
    id: uuid.UUID
    address_type: str
    name: str
    phone: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str

    model_config = {"from_attributes": True}


class PackageResponse(BaseModel):
    id: uuid.UUID
    length_cm: float
    breadth_cm: float
    height_cm: float
    actual_weight_kg: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    pickup_zone_id: uuid.UUID | None
    drop_zone_id: uuid.UUID | None
    order_type: OrderType
    payment_type: PaymentType
    zone_type: ZoneType | None
    actual_weight: float
    volumetric_weight: float
    billable_weight: float
    base_charge: float
    cod_charge: float
    total_charge: float
    status: OrderStatus
    assigned_agent_id: uuid.UUID | None
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    addresses: list[AddressResponse] = []
    package: PackageResponse | None = None

    model_config = {"from_attributes": True}


class StatusUpdateRequest(BaseModel):
    status: OrderStatus
    remarks: str | None = None


class AdminStatusUpdateRequest(BaseModel):
    status: OrderStatus
    reason: str = Field(..., min_length=5, description="Reason for admin override (required for audit)")
