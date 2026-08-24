# Last-Mile Delivery Tracker — Backend API

A production-style **FastAPI** backend for a Last-Mile Delivery Tracker platform.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.x-orange.svg)](https://docs.sqlalchemy.org/)

---

## 1. Project Overview

The backend is the **single source of truth** for:

- Price calculation (B2B/B2C, intra/inter-zone, volumetric weight)
- Order creation and lifecycle management
- Delivery agent assignment (manual + auto via Haversine)
- Immutable tracking history
- Failed delivery and rescheduling workflows
- Email/SMS notifications (provider-agnostic abstraction)
- Role-based access control (CUSTOMER, AGENT, ADMIN)

---

## 2. Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── core/                   # Config, DB, security, DI, exceptions
│   ├── models/                 # SQLAlchemy ORM models (15 tables)
│   ├── schemas/                # Pydantic v2 request/response schemas
│   ├── repositories/           # Data-access layer (pure DB queries)
│   ├── services/               # Business logic layer
│   ├── api/v1/                 # FastAPI route handlers
│   └── utils/                  # Haversine, order number, pagination
├── migrations/                 # Alembic async migrations
├── tests/                      # pytest test suite (25+ test cases)
├── scripts/seed.py             # Development seed data
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

**Layers:**

```
API Routes → Services → Repositories → Database
                ↓
          Notifications (BackgroundTasks)
```

---

## 3. Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI 0.115 (async) |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + Argon2 (argon2-cffi) |
| Config | pydantic-settings + python-dotenv |
| Email | aiosmtplib (async SMTP) |
| SMS | Twilio (abstracted, optional) |
| HTTP Client | httpx |
| Tests | pytest + pytest-asyncio + httpx |
| Containers | Docker + docker-compose |

---

## 4. Environment Setup

### 4.1 Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (optional but recommended)

### 4.2 Local Setup

```bash
# Clone / navigate to backend
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET_KEY etc.
```

---

## 5. .env.example Explanation

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async URL: `postgresql+asyncpg://user:pass@host:port/db` |
| `JWT_SECRET_KEY` | Random 32-byte hex: `openssl rand -hex 32` |
| `JWT_ALGORITHM` | HS256 (recommended) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (default: 60) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (default: 7) |
| `SMTP_HOST/PORT/USERNAME/PASSWORD` | SMTP config for email |
| `EMAIL_DISABLED` | Set `true` in dev to skip email (no-op mode) |
| `TWILIO_ACCOUNT_SID/AUTH_TOKEN` | Twilio SMS credentials |
| `SMS_DISABLED` | Set `true` in dev to skip SMS |
| `REDIS_URL` | Redis URL for future Celery integration |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins |
| `VOLUMETRIC_DIVISOR` | Divisor for volumetric weight (default: 5000) |

---

## 6. PostgreSQL Setup

```bash
# Create database and user
psql -U postgres
CREATE USER lmd_user WITH PASSWORD 'lmd_password';
CREATE DATABASE lmd_db OWNER lmd_user;
GRANT ALL PRIVILEGES ON DATABASE lmd_db TO lmd_user;
\q
```

---

## 7. Alembic Migrations

```bash
# Apply all migrations
alembic upgrade head

# Generate new migration after model changes
alembic revision --autogenerate -m "your_migration_name"

# Downgrade one step
alembic downgrade -1
```

---

## 8. Seed Data

```bash
# Run the seed script (requires migrations applied)
python scripts/seed.py
```

**Seeded accounts:**

| Role | Email | Password |
|---|---|---|
| Admin | admin@lmdtracker.com | Admin@12345 |
| Customer | priya@example.com | Customer@123 |
| Agent | rajan@lmdtracker.com | Agent@12345 |

**Seeded data includes:**
- 5 zones (Mumbai North, Mumbai South, Pune, Chennai, Bangalore)
- 10 areas with postal codes
- B2C/B2B rate cards (intra + inter zone, 5 weight slabs each)
- COD surcharges (B2C: ₹30 fixed, B2B: 2% of base)
- 4 delivery agents

---

## 9. Running the Application

### Option A — Docker Compose (Recommended)

```bash
cd backend
docker-compose up -d

# Apply migrations
docker-compose exec api alembic upgrade head

# Seed data
docker-compose exec api python scripts/seed.py

# View logs
docker-compose logs -f api
```

### Option B — Local

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 10. Running Tests

```bash
cd backend

# Install test dependencies (already in requirements.txt)
pip install aiosqlite  # SQLite async driver for test DB

# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_rate_engine.py -v
```

**Test coverage:**
- Authentication (register, login, JWT, role auth)
- Rate engine (zone detection, volumetric weight, B2B/B2C pricing, COD)
- Order creation
- Status machine transitions
- Immutable tracking history
- Manual + auto agent assignment
- Haversine distance calculation
- Agent availability enforcement
- Failed delivery workflow
- Rescheduling
- Admin override with audit log
- Notification failure isolation

---

## 11. Swagger / API Documentation

Once running:

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc documentation |
| http://localhost:8000/openapi.json | Raw OpenAPI schema |
| http://localhost:8000/health | Health check |

**To authenticate in Swagger:**
1. Call `POST /api/v1/auth/login`
2. Copy the `access_token`
3. Click the **Authorize** button → enter `Bearer <token>`

---

## 12. Authentication Flow

```
POST /api/v1/auth/register  →  Create account
POST /api/v1/auth/login     →  Get access_token + refresh_token
GET  /api/v1/auth/me        →  Verify token + get profile
POST /api/v1/auth/refresh   →  Renew access token
```

Passwords are hashed with **Argon2** (industry-best-practice KDF).  
Tokens use **HS256 JWT** with configurable expiry.

---

## 13. Rate Calculation Logic

The rate engine follows a strict 9-step algorithm:

```
1. Detect pickup zone: postal_code → areas → zones
2. Detect drop zone:   postal_code → areas → zones
3. Volumetric weight = (length × breadth × height) / 5000
4. Billable weight   = max(actual_weight, volumetric_weight)
5. Zone type         = INTRA_ZONE (same zone) | INTER_ZONE (different)
6. Lookup rate card: order_type + zone_type + billable_weight slab
7. Base charge       = rate_card.price
8. COD surcharge     = FIXED or PERCENTAGE (if payment_type == COD)
9. Total charge      = base_charge + cod_surcharge
```

**Important:** Rates are **never hardcoded**. All pricing comes from the `rate_cards` and `cod_surcharges` database tables, manageable by admins via the API.

**Frontend integration pattern:**
```
POST /api/v1/orders/calculate  →  Show price to user (no order created)
User confirms
POST /api/v1/orders            →  Create order (rate recalculated server-side)
```

---

## 14. Zone Detection

Postal code → `areas.postal_code` → `areas.zone_id` → `zones`.

This is a simple, fast DB lookup. The `ZoneService` has a clean interface that can be replaced with a geo-provider (Google Maps, etc.) without changing the rate engine or order service.

---

## 15. Agent Assignment

### Manual Assignment
Admin selects a specific agent. Row-level `SELECT FOR UPDATE SKIP LOCKED` prevents concurrent double-assignment.

### Auto Assignment Algorithm
1. Find AVAILABLE agents in the pickup zone first.
2. If none → find all AVAILABLE agents globally.
3. Sort by Haversine distance to pickup location.
4. Select the nearest eligible agent.
5. Lock agent row before assignment.

After delivery: order → DELIVERED → agent automatically set to AVAILABLE.

---

## 16. Failed Delivery Flow

```
Agent calls: POST /api/v1/agent/orders/{id}/fail
  Body: { "reason": "CUSTOMER_NOT_AVAILABLE", "remarks": "..." }

System:
  1. Validate agent owns this order
  2. Validate order is OUT_FOR_DELIVERY
  3. Update order status → FAILED
  4. Insert immutable status history record
  5. Close current delivery attempt (outcome=FAILED)
  6. Release the agent (AVAILABLE)
  7. Notify customer (non-fatal)

Customer:
  POST /api/v1/orders/{id}/reschedule
  Body: { "new_delivery_date": "2026-08-25" }

System:
  1. Validate order is FAILED
  2. Create reschedule_requests record
  3. Create new delivery_attempt
  4. Release previous agent
  5. Reset order to CREATED
  6. Insert immutable history record
  7. Notify customer
```

---

## 17. Notification Flow

```
Service layer calls NotificationService.notify_order_event(event, order, user)
  ↓
Dispatched in try/except — provider failure is caught and logged
  ↓
EMAIL:  aiosmtplib async SMTP (no-op in dev when EMAIL_DISABLED=true)
SMS:    Twilio (no-op in dev when SMS_DISABLED=true)
  ↓
Result stored in notifications table (SENT | FAILED | PENDING)
  ↓
Order transaction is committed REGARDLESS of notification outcome
```

---

## 18. API Endpoint Reference

### Authentication
| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /api/v1/auth/register | None | Register new user |
| POST | /api/v1/auth/login | None | Login, get JWT |
| POST | /api/v1/auth/refresh | None | Refresh access token |
| GET | /api/v1/auth/me | Any | Current user profile |

### Customer — Orders
| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /api/v1/orders/calculate | CUSTOMER | Calculate price (no order created) |
| POST | /api/v1/orders | CUSTOMER | Create order |
| GET | /api/v1/orders | CUSTOMER | List my orders |
| GET | /api/v1/orders/{id} | CUSTOMER | Get order detail |
| GET | /api/v1/orders/{id}/tracking | Any | Tracking timeline |
| POST | /api/v1/orders/{id}/reschedule | CUSTOMER | Reschedule failed order |

### Agent
| Method | URL | Auth | Description |
|---|---|---|---|
| GET | /api/v1/agent/profile | AGENT | Agent profile |
| GET | /api/v1/agent/orders | AGENT | Assigned orders |
| GET | /api/v1/agent/orders/{id} | AGENT | Order detail |
| PATCH | /api/v1/agent/location | AGENT | Update GPS location |
| PATCH | /api/v1/agent/availability | AGENT | Update availability |
| PATCH | /api/v1/agent/orders/{id}/status | AGENT | Update delivery status |
| POST | /api/v1/agent/orders/{id}/fail | AGENT | Mark delivery failed |

### Admin — Zones
| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /api/v1/admin/zones | ADMIN | Create zone |
| GET | /api/v1/admin/zones | ADMIN | List zones |
| GET | /api/v1/admin/zones/{id} | ADMIN | Get zone |
| PATCH | /api/v1/admin/zones/{id} | ADMIN | Update zone |
| DELETE | /api/v1/admin/zones/{id} | ADMIN | Delete zone |

### Admin — Areas
| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /api/v1/admin/areas | ADMIN | Create area |
| GET | /api/v1/admin/areas | ADMIN | List areas |
| GET | /api/v1/admin/areas/{id} | ADMIN | Get area |
| PATCH | /api/v1/admin/areas/{id} | ADMIN | Update area |
| DELETE | /api/v1/admin/areas/{id} | ADMIN | Delete area |

### Admin — Rate Cards
| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /api/v1/admin/rates | ADMIN | Create rate card |
| GET | /api/v1/admin/rates | ADMIN | List rate cards |
| GET | /api/v1/admin/rates/{id} | ADMIN | Get rate card |
| PATCH | /api/v1/admin/rates/{id} | ADMIN | Update rate card |
| DELETE | /api/v1/admin/rates/{id} | ADMIN | Delete rate card |

### Admin — COD Surcharges
| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /api/v1/admin/cod-surcharges | ADMIN | Create COD surcharge |
| GET | /api/v1/admin/cod-surcharges | ADMIN | List COD surcharges |
| PATCH | /api/v1/admin/cod-surcharges/{id} | ADMIN | Update COD surcharge |
| DELETE | /api/v1/admin/cod-surcharges/{id} | ADMIN | Delete COD surcharge |

### Admin — Orders
| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /api/v1/admin/orders | ADMIN | Create order for customer |
| GET | /api/v1/admin/orders | ADMIN | List orders (with filters) |
| GET | /api/v1/admin/orders/{id} | ADMIN | Get order |
| PATCH | /api/v1/admin/orders/{id}/status | ADMIN | Override status (audited) |
| POST | /api/v1/admin/orders/{id}/assign-agent | ADMIN | Manual assignment |
| POST | /api/v1/admin/orders/{id}/auto-assign | ADMIN | Auto assignment |

---

## 19. Database Schema

```
User
├── DeliveryAgent (1:1)
├── Orders (as customer)
└── Notifications

Zone
└── Area (1:N, via postal_code)

Order
├── OrderAddress (PICKUP + DROP)
├── OrderPackage (dimensions)
├── OrderStatusHistory (append-only)
├── AgentAssignment (history)
├── DeliveryAttempt (each physical attempt)
├── RescheduleRequest
└── Notification

RateCard (order_type × zone_type × weight_slab)
CODSurcharge (per order_type)
AuditLog (admin actions)
```

**Order Status Machine:**
```
CREATED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED
                                                     → FAILED → (reschedule) → CREATED
CREATED/PICKED_UP/IN_TRANSIT → CANCELLED
```

---

## 20. Deployment

### Render

1. Create a new Web Service → select your repository
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add a PostgreSQL instance and set `DATABASE_URL` env var
5. Run migrations: add `alembic upgrade head` to the start command or a release command

### Railway

1. Connect repository
2. Add PostgreSQL and Redis services
3. Set all env vars from `.env.example`
4. Railway auto-detects the Dockerfile and builds it

### Production Checklist

- [ ] Set `JWT_SECRET_KEY` to a cryptographically random value
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `EMAIL_DISABLED=false` and configure SMTP
- [ ] Set `SMS_DISABLED=false` and configure Twilio
- [ ] Use a managed PostgreSQL (e.g., Supabase, Neon, Railway, RDS)
- [ ] Enable SSL for database connections
- [ ] Set `CORS_ALLOWED_ORIGINS` to your actual frontend domain
- [ ] Use a reverse proxy (nginx) in front of uvicorn
- [ ] Set up log aggregation (e.g., Datadog, CloudWatch)
- [ ] Configure automated database backups
