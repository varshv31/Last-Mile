# Last-Mile Delivery Tracker — API Documentation

**Base URL:** `http://localhost:8000`
**API Version:** `v1`
**Prefix:** `/api/v1`
**Auth:** JWT Bearer Token

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Customer — Orders](#2-customer--orders)
3. [Agent](#3-agent)
4. [Admin — Zones](#4-admin--zones)
5. [Admin — Areas](#5-admin--areas)
6. [Admin — Rate Cards](#6-admin--rate-cards)
7. [Admin — COD Surcharges](#7-admin--cod-surcharges)
8. [Admin — Orders](#8-admin--orders)
9. [Health Check](#9-health-check)
10. [Schemas Reference](#10-schemas-reference)
11. [Enums Reference](#11-enums-reference)
12. [Error Responses](#12-error-responses)

---

## 1. Authentication

> No auth required for register/login/refresh.

---

### POST `/api/v1/auth/register`

Register a new user account.

**Request Body**
```json
{
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "phone": "+919876543210",
  "password": "SecurePass123!",
  "role": "CUSTOMER"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | YES | 2-255 characters |
| `email` | string | YES | Must be unique |
| `phone` | string | NO | Max 20 chars |
| `password` | string | YES | 8-128 characters |
| `role` | enum | NO | CUSTOMER (default), AGENT, ADMIN |

**Response 201 Created**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "phone": "+919876543210",
  "role": "CUSTOMER",
  "is_active": true,
  "created_at": "2026-08-23T06:00:00Z",
  "updated_at": "2026-08-23T06:00:00Z"
}
```

**Errors:** 409 Conflict (email taken), 422 Validation error

---

### POST `/api/v1/auth/login`

Authenticate and receive JWT tokens.

**Request Body**
```json
{ "email": "priya@example.com", "password": "Customer@123" }
```

**Response 200 OK**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:** 401 Invalid credentials

---

### POST `/api/v1/auth/refresh`

Exchange refresh token for new token pair.

**Request Body**
```json
{ "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```

**Response 200 OK** - Same as login response

**Errors:** 401 Invalid or expired refresh token

---

### GET `/api/v1/auth/me`

**Auth:** Bearer Token required

Get current authenticated user profile.

**Response 200 OK** - UserResponse object (see Schemas)

**Errors:** 401 Not authenticated

---

## 2. Customer — Orders

> All endpoints require CUSTOMER role JWT.

---

### POST `/api/v1/orders/calculate`

Calculate delivery charges WITHOUT creating an order.

**Request Body**
```json
{
  "pickup_address": {
    "name": "Sender Name",
    "phone": "9876543210",
    "address_line1": "123 MG Road",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400069"
  },
  "drop_address": {
    "name": "Receiver Name",
    "phone": "9123456789",
    "address_line1": "45 Anna Nagar",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "postal_code": "600040"
  },
  "package": {
    "length_cm": 20,
    "breadth_cm": 15,
    "height_cm": 10,
    "actual_weight_kg": 1.5
  },
  "order_type": "B2C",
  "payment_type": "COD"
}
```

**Response 200 OK**
```json
{
  "pickup_area_name": "Andheri East",
  "pickup_postal_code": "400069",
  "pickup_zone_id": "uuid-of-pickup-zone",
  "pickup_zone_name": "Mumbai North",
  "drop_area_name": "T Nagar",
  "drop_postal_code": "600040",
  "drop_zone_id": "uuid-of-drop-zone",
  "drop_zone_name": "Chennai",
  "zone_type": "INTER_ZONE",
  "actual_weight": 1.5,
  "volumetric_weight": 0.6,
  "billable_weight": 1.5,
  "rate_card_id": "uuid-of-rate-card",
  "base_charge": 120.0,
  "cod_surcharge": 30.0,
  "total_charge": 150.0,
  "order_type": "B2C",
  "payment_type": "COD"
}
```

**Errors:** 400 Zone/rate not configured, 401 Unauthenticated

---

### POST `/api/v1/orders`

Create a delivery order. Rate is recalculated server-side.

**Request Body** - Same as /calculate above (without postal_code shorthand, use full address)

**Response 201 Created**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "order_number": "LMD-20260823-ABCD",
  "customer_id": "uuid-of-customer",
  "pickup_zone_id": "uuid-of-zone",
  "drop_zone_id": "uuid-of-zone",
  "order_type": "B2C",
  "payment_type": "PREPAID",
  "zone_type": "INTER_ZONE",
  "actual_weight": 2.0,
  "volumetric_weight": 1.8,
  "billable_weight": 2.0,
  "base_charge": 120.0,
  "cod_charge": 0.0,
  "total_charge": 120.0,
  "status": "CREATED",
  "assigned_agent_id": null,
  "confirmed_at": null,
  "created_at": "2026-08-23T06:00:00Z",
  "updated_at": "2026-08-23T06:00:00Z",
  "addresses": [
    {
      "id": "uuid",
      "address_type": "PICKUP",
      "name": "Sender",
      "phone": "9876543210",
      "address_line1": "10 Linking Road",
      "address_line2": null,
      "city": "Mumbai",
      "state": "Maharashtra",
      "postal_code": "400069",
      "country": "India"
    },
    {
      "id": "uuid",
      "address_type": "DROP",
      "name": "Receiver",
      "phone": "9000000001",
      "address_line1": "5 T Nagar",
      "address_line2": null,
      "city": "Chennai",
      "state": "Tamil Nadu",
      "postal_code": "600040",
      "country": "India"
    }
  ],
  "package": {
    "id": "uuid",
    "length_cm": 30,
    "breadth_cm": 20,
    "height_cm": 15,
    "actual_weight_kg": 2.0
  }
}
```

---

### GET `/api/v1/orders`

List all orders for the authenticated customer.

**Query Params:** `limit` (default 20, max 100), `offset` (default 0)

**Response 200 OK** - Array of OrderResponse objects

---

### GET `/api/v1/orders/{order_id}`

**Path Params:** `order_id` (UUID)

**Response 200 OK** - OrderResponse object

**Errors:** 404 Not found

---

### GET `/api/v1/orders/{order_id}/tracking`

Get full chronological tracking timeline.

**Response 200 OK**
```json
{
  "order_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "order_number": "LMD-20260823-ABCD",
  "current_status": "IN_TRANSIT",
  "timeline": [
    {
      "id": "uuid",
      "previous_status": null,
      "new_status": "CREATED",
      "actor_role": "CUSTOMER",
      "actor_name": "Priya Sharma",
      "remarks": null,
      "created_at": "2026-08-23T06:00:00Z"
    },
    {
      "id": "uuid",
      "previous_status": "CREATED",
      "new_status": "PICKED_UP",
      "actor_role": "AGENT",
      "actor_name": "Rajan Kumar",
      "remarks": "Package collected",
      "created_at": "2026-08-23T07:30:00Z"
    }
  ]
}
```

**Errors:** 404 Not found

---

### POST `/api/v1/orders/{order_id}/reschedule`

Reschedule a FAILED delivery.

**Request Body**
```json
{ "new_delivery_date": "2026-08-25" }
```

**Response 201 Created**
```json
{
  "order_id": "uuid",
  "reschedule_id": "uuid",
  "new_delivery_date": "2026-08-25",
  "status": "CREATED"
}
```

**Errors:** 400 Order not eligible, 404 Not found

---

## 3. Agent

> All endpoints require AGENT role JWT.

---

### GET `/api/v1/agent/profile`

**Response 200 OK**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "availability_status": "AVAILABLE",
  "current_latitude": 19.076,
  "current_longitude": 72.8777,
  "current_zone_id": "uuid",
  "created_at": "2026-08-23T06:00:00Z",
  "updated_at": "2026-08-23T06:00:00Z"
}
```

---

### GET `/api/v1/agent/orders`

List orders assigned to this agent.

**Query Params:** `limit` (default 20), `offset` (default 0)

**Response 200 OK** - Array of OrderResponse objects

---

### GET `/api/v1/agent/orders/{order_id}`

**Response 200 OK** - OrderResponse object

**Errors:** 404 Not found or not assigned to agent

---

### PATCH `/api/v1/agent/location`

Update GPS coordinates.

**Request Body**
```json
{
  "latitude": 19.076,
  "longitude": 72.8777,
  "zone_id": "uuid-optional"
}
```

| Field | Constraints |
|-------|-------------|
| latitude | -90 to 90, required |
| longitude | -180 to 180, required |
| zone_id | UUID, optional |

**Response 200 OK** - Updated AgentProfileResponse

---

### PATCH `/api/v1/agent/availability`

**Request Body**
```json
{ "availability_status": "AVAILABLE" }
```

Values: `AVAILABLE`, `BUSY`, `OFFLINE`

**Response 200 OK** - Updated AgentProfileResponse

---

### PATCH `/api/v1/agent/orders/{order_id}/status`

Update delivery status. Only valid state-machine transitions allowed. Creates immutable history entry.

**Request Body**
```json
{
  "status": "PICKED_UP",
  "remarks": "Package collected from sender"
}
```

**Valid transitions:**
```
CREATED -> PICKED_UP -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED
CREATED / PICKED_UP / IN_TRANSIT -> CANCELLED
```

**Response 200 OK** - Updated OrderResponse

**Errors:** 400 Invalid transition, 403 Not assigned to agent, 404 Not found

---

### POST `/api/v1/agent/orders/{order_id}/fail`

Mark delivery as FAILED. Order must be in OUT_FOR_DELIVERY status. Agent is auto-released.

**Request Body**
```json
{
  "reason": "CUSTOMER_NOT_AVAILABLE",
  "remarks": "Customer did not respond to calls."
}
```

FailureReason values: `CUSTOMER_NOT_AVAILABLE`, `WRONG_ADDRESS`, `CUSTOMER_REJECTED`, `ACCESS_ISSUE`, `OTHER`

**Response 200 OK** - Updated OrderResponse with status FAILED

**Errors:** 400 Not in OUT_FOR_DELIVERY, 403 Not assigned to agent

---

## 4. Admin — Zones

> All endpoints require ADMIN role JWT.

---

### POST `/api/v1/admin/zones`

**Request Body**
```json
{
  "name": "Mumbai North",
  "code": "MUM-N",
  "description": "Northern Mumbai zone",
  "is_active": true
}
```

**Response 201 Created**
```json
{
  "id": "uuid",
  "name": "Mumbai North",
  "code": "MUM-N",
  "description": "Northern Mumbai zone",
  "is_active": true,
  "created_at": "2026-08-23T06:00:00Z",
  "updated_at": "2026-08-23T06:00:00Z"
}
```

---

### GET `/api/v1/admin/zones`

**Query Params:** `limit` (default 100, max 500), `offset` (default 0)

**Response 200 OK** - Array of ZoneResponse

---

### GET `/api/v1/admin/zones/{zone_id}`

**Response 200 OK** - ZoneResponse

---

### PATCH `/api/v1/admin/zones/{zone_id}`

**Request Body** (all fields optional)
```json
{ "name": "Updated Name", "description": "New desc", "is_active": false }
```

**Response 200 OK** - Updated ZoneResponse

---

### DELETE `/api/v1/admin/zones/{zone_id}`

**Response 204 No Content**

---

## 5. Admin — Areas

> All endpoints require ADMIN role JWT. Areas map postal codes to zones.

---

### POST `/api/v1/admin/areas`

**Request Body**
```json
{
  "name": "Andheri East",
  "postal_code": "400069",
  "zone_id": "uuid-of-zone",
  "is_active": true
}
```

**Response 201 Created**
```json
{
  "id": "uuid",
  "name": "Andheri East",
  "postal_code": "400069",
  "zone_id": "uuid-of-zone",
  "is_active": true,
  "created_at": "2026-08-23T06:00:00Z",
  "updated_at": "2026-08-23T06:00:00Z"
}
```

---

### GET `/api/v1/admin/areas`

**Query Params:** `limit` (default 100), `offset` (default 0)

**Response 200 OK** - Array of AreaResponse

---

### GET `/api/v1/admin/areas/{area_id}`

**Response 200 OK** - AreaResponse

---

### PATCH `/api/v1/admin/areas/{area_id}`

**Request Body** (all optional)
```json
{ "name": "New Name", "zone_id": "new-zone-uuid", "is_active": false }
```

**Response 200 OK** - Updated AreaResponse

---

### DELETE `/api/v1/admin/areas/{area_id}`

**Response 204 No Content**

---

## 6. Admin — Rate Cards

> All endpoints require ADMIN role JWT.

Rate cards define: order_type x zone_type x weight_slab => price

---

### POST `/api/v1/admin/rates`

**Request Body**
```json
{
  "order_type": "B2C",
  "zone_type": "INTRA_ZONE",
  "min_weight": 0,
  "max_weight": 1,
  "price": 40.0,
  "is_active": true,
  "effective_from": "2026-01-01",
  "effective_to": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| order_type | enum | YES | B2B or B2C |
| zone_type | enum | YES | INTRA_ZONE or INTER_ZONE |
| min_weight | float | YES | Lower kg bound (>=0) |
| max_weight | float | YES | Upper kg bound (>0) |
| price | float | YES | Price in INR (>0) |
| is_active | bool | NO | Default true |
| effective_from | date | NO | YYYY-MM-DD |
| effective_to | date | NO | YYYY-MM-DD |

**Response 201 Created**
```json
{
  "id": "uuid",
  "order_type": "B2C",
  "zone_type": "INTRA_ZONE",
  "min_weight": 0,
  "max_weight": 1,
  "price": 40.0,
  "is_active": true,
  "effective_from": "2026-01-01",
  "effective_to": null,
  "created_at": "2026-08-23T06:00:00Z",
  "updated_at": "2026-08-23T06:00:00Z"
}
```

---

### GET `/api/v1/admin/rates`

**Query Params:** `limit` (default 100), `offset` (default 0)

**Response 200 OK** - Array of RateCardResponse

---

### GET `/api/v1/admin/rates/{rate_id}`

**Response 200 OK** - RateCardResponse

---

### PATCH `/api/v1/admin/rates/{rate_id}`

**Request Body** (all optional)
```json
{ "price": 55.0, "is_active": true, "effective_from": "2026-09-01", "effective_to": null }
```

**Response 200 OK** - Updated RateCardResponse

---

### DELETE `/api/v1/admin/rates/{rate_id}`

**Response 204 No Content**

---

## 7. Admin — COD Surcharges

> All endpoints require ADMIN role JWT.

Applies when payment_type == COD. Can be FIXED (flat INR) or PERCENTAGE (% of base charge).

---

### POST `/api/v1/admin/cod-surcharges`

**Request Body**
```json
{
  "order_type": "B2C",
  "surcharge_type": "FIXED",
  "value": 30.0,
  "is_active": true
}
```

**Response 201 Created**
```json
{
  "id": "uuid",
  "order_type": "B2C",
  "surcharge_type": "FIXED",
  "value": 30.0,
  "is_active": true,
  "created_at": "2026-08-23T06:00:00Z",
  "updated_at": "2026-08-23T06:00:00Z"
}
```

---

### GET `/api/v1/admin/cod-surcharges`

**Response 200 OK** - Array of CODSurchargeResponse

---

### PATCH `/api/v1/admin/cod-surcharges/{id}`

**Request Body** (all optional)
```json
{ "surcharge_type": "PERCENTAGE", "value": 2.0, "is_active": true }
```

**Response 200 OK** - Updated CODSurchargeResponse

---

### DELETE `/api/v1/admin/cod-surcharges/{id}`

**Response 204 No Content**

---

## 8. Admin — Orders

> All endpoints require ADMIN role JWT.

---

### POST `/api/v1/admin/orders`

Create an order on behalf of a customer.

**Request Body**
```json
{
  "pickup_address": {
    "name": "Sender", "phone": "9876543210",
    "address_line1": "10 Linking Road", "city": "Mumbai",
    "state": "Maharashtra", "postal_code": "400069"
  },
  "drop_address": {
    "name": "Receiver", "phone": "9000000001",
    "address_line1": "5 T Nagar", "city": "Chennai",
    "state": "Tamil Nadu", "postal_code": "600040"
  },
  "package": {
    "length_cm": 30, "breadth_cm": 20, "height_cm": 15, "actual_weight_kg": 2.0
  },
  "order_type": "B2C",
  "payment_type": "PREPAID",
  "customer_id": "uuid-of-customer"
}
```

**Response 201 Created** - OrderResponse object

---

### GET `/api/v1/admin/orders`

List all orders with filters.

**Query Parameters**

| Param | Type | Description |
|-------|------|-------------|
| status | enum | Filter by OrderStatus |
| pickup_zone_id | UUID | Filter by pickup zone |
| drop_zone_id | UUID | Filter by drop zone |
| agent_id | UUID | Filter by assigned agent |
| order_type | enum | B2B or B2C |
| payment_type | enum | PREPAID or COD |
| customer_id | UUID | Filter by customer |
| created_from | datetime | Created after timestamp |
| created_to | datetime | Created before timestamp |
| limit | integer | Default 20, max 100 |
| offset | integer | Default 0 |

**Response 200 OK** - Array of OrderResponse

---

### GET `/api/v1/admin/orders/{order_id}`

**Response 200 OK** - OrderResponse

---

### PATCH `/api/v1/admin/orders/{order_id}/status`

Override order status (creates audit log).

**Request Body**
```json
{
  "status": "CANCELLED",
  "reason": "Customer requested cancellation via support ticket #1234"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| status | YES | Target OrderStatus |
| reason | YES | Min 5 chars, stored in audit log |

**Response 200 OK** - Updated OrderResponse

---

### POST `/api/v1/admin/orders/{order_id}/assign-agent`

Manually assign a specific agent.

**Request Body**
```json
{ "agent_id": "uuid-of-agent-user" }
```

Note: agent_id is the agent's USER UUID, not delivery_agents record UUID.

**Response 201 Created**
```json
{
  "agent_user_id": "uuid",
  "agent_name": "Rajan Kumar",
  "assignment_type": "MANUAL",
  "distance_km": null,
  "reason": "Manual assignment by admin",
  "assigned_at": "2026-08-23T07:00:00Z"
}
```

---

### POST `/api/v1/admin/orders/{order_id}/auto-assign`

Auto-assign nearest available agent using Haversine distance.

Algorithm:
1. Find AVAILABLE agents in pickup zone
2. If none -> search all AVAILABLE agents globally
3. Sort by Haversine distance to pickup location
4. Select nearest with row-level lock

**No Request Body**

**Response 201 Created**
```json
{
  "agent_user_id": "uuid",
  "agent_name": "Rajan Kumar",
  "assignment_type": "AUTO",
  "distance_km": 3.7,
  "reason": "Nearest available agent in pickup zone",
  "assigned_at": "2026-08-23T07:00:00Z"
}
```

---

## 9. Health Check

---

### GET `/health`

**Response 200 OK**
```json
{ "status": "ok" }
```

---

## 10. Schemas Reference

### AddressInput (request)
```json
{
  "name": "string (1-255, required)",
  "phone": "string (max 20, required)",
  "address_line1": "string (1-500, required)",
  "address_line2": "string | null",
  "city": "string (1-255, required)",
  "state": "string (1-255, required)",
  "postal_code": "string (1-20, required)",
  "country": "string (default: India)"
}
```

### PackageInput (request)
```json
{
  "length_cm": "float (>0, required)",
  "breadth_cm": "float (>0, required)",
  "height_cm": "float (>0, required)",
  "actual_weight_kg": "float (>0, required)"
}
```

### OrderResponse (full order object)
```json
{
  "id": "UUID",
  "order_number": "string (LMD-YYYYMMDD-XXXX)",
  "customer_id": "UUID",
  "pickup_zone_id": "UUID | null",
  "drop_zone_id": "UUID | null",
  "order_type": "B2B | B2C",
  "payment_type": "PREPAID | COD",
  "zone_type": "INTRA_ZONE | INTER_ZONE | null",
  "actual_weight": "float (kg)",
  "volumetric_weight": "float (L*B*H / 5000)",
  "billable_weight": "float (max of actual, volumetric)",
  "base_charge": "float (INR)",
  "cod_charge": "float (INR, 0 if PREPAID)",
  "total_charge": "float (base + cod)",
  "status": "OrderStatus",
  "assigned_agent_id": "UUID | null",
  "confirmed_at": "datetime | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "addresses": "[AddressResponse]",
  "package": "PackageResponse | null"
}
```

### UserResponse
```json
{
  "id": "UUID",
  "name": "string",
  "email": "string",
  "phone": "string | null",
  "role": "CUSTOMER | AGENT | ADMIN",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### TrackingTimelineResponse
```json
{
  "order_id": "UUID",
  "order_number": "string",
  "current_status": "OrderStatus",
  "timeline": [
    {
      "id": "UUID",
      "previous_status": "OrderStatus | null",
      "new_status": "OrderStatus",
      "actor_role": "CUSTOMER | AGENT | ADMIN | null",
      "actor_name": "string | null",
      "remarks": "string | null",
      "created_at": "datetime"
    }
  ]
}
```

### AgentProfileResponse
```json
{
  "id": "UUID",
  "user_id": "UUID",
  "availability_status": "AVAILABLE | BUSY | OFFLINE",
  "current_latitude": "float | null",
  "current_longitude": "float | null",
  "current_zone_id": "UUID | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### AssignmentResponse
```json
{
  "agent_user_id": "UUID",
  "agent_name": "string",
  "assignment_type": "MANUAL | AUTO",
  "distance_km": "float | null",
  "reason": "string",
  "assigned_at": "datetime"
}
```

---

## 11. Enums Reference

| Enum | Values |
|------|--------|
| UserRole | CUSTOMER, AGENT, ADMIN |
| OrderStatus | CREATED, PICKED_UP, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, FAILED, CANCELLED |
| OrderType | B2B, B2C |
| PaymentType | PREPAID, COD |
| ZoneType | INTRA_ZONE, INTER_ZONE |
| AvailabilityStatus | AVAILABLE, BUSY, OFFLINE |
| AssignmentType | MANUAL, AUTO |
| SurchargeType | FIXED, PERCENTAGE |
| FailureReason | CUSTOMER_NOT_AVAILABLE, WRONG_ADDRESS, CUSTOMER_REJECTED, ACCESS_ISSUE, OTHER |

---

## 12. Error Responses

```json
{ "detail": "Human-readable error message" }
```

Validation errors (422):
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Resource created |
| 204 | Deleted, no content |
| 400 | Bad request / business logic error |
| 401 | Unauthenticated |
| 403 | Forbidden (wrong role or not owner) |
| 404 | Not found |
| 409 | Conflict (duplicate email) |
| 422 | Validation error |
| 500 | Internal server error |

---

## Quick Start (curl)

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"priya@example.com","password":"Customer@123"}'

# Calculate price
curl -X POST http://localhost:8000/api/v1/orders/calculate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"pickup_address":{"name":"S","phone":"9876543210","address_line1":"10 Linking Road","city":"Mumbai","state":"Maharashtra","postal_code":"400069"},"drop_address":{"name":"R","phone":"9000000001","address_line1":"5 T Nagar","city":"Chennai","state":"Tamil Nadu","postal_code":"600040"},"package":{"length_cm":30,"breadth_cm":20,"height_cm":15,"actual_weight_kg":2.0},"order_type":"B2C","payment_type":"PREPAID"}'

# Track order
curl http://localhost:8000/api/v1/orders/<order_id>/tracking \
  -H "Authorization: Bearer <token>"
```

---

*Generated from live OpenAPI spec — Last-Mile Delivery Tracker v1.0.0*
