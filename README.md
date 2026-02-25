# SaaS Platform API

A production-ready FastAPI backend for a multi-role SaaS marketplace with Stripe payments.

## Tech Stack

| Layer | Tool |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| DB | PostgreSQL (SQLite for dev) |
| Auth | JWT (access + refresh tokens) |
| Passwords | Argon2 (via passlib) |
| Payments | Stripe PaymentIntents |
| Migrations | Alembic |
| Validation | Pydantic v2 |

---

## Project Structure

```
saas-platform/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py        # /auth/*
│   │       │   ├── products.py    # /products/*
│   │       │   ├── cart.py        # /cart/*
│   │       │   ├── orders.py      # /checkout, /orders/*, /webhooks/*
│   │       │   └── admin.py       # /admin/*
│   │       └── router.py
│   ├── core/
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── database.py            # Engine, SessionLocal, get_db
│   │   ├── security.py            # JWT, password hashing
│   │   └── permissions.py         # RBAC dependencies
│   ├── models/
│   │   ├── user.py                # User, UserRole
│   │   ├── product.py             # Product
│   │   ├── cart.py                # Cart, CartItem
│   │   └── order.py               # Order, OrderItem, Payment
│   ├── schemas/
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   └── order.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── cart_service.py
│   │   └── order_service.py
│   ├── middleware/
│   │   └── rate_limit.py
│   └── main.py
├── requirements.txt
├── .env.example
└── alembic.ini
```

---

## Quick Start

### 1. Clone & install
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and SECRET_KEY
openssl rand -hex 32   # use output as SECRET_KEY
```

### 3. Run (dev)
```bash
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

### 4. Migrations (production)
```bash
alembic init alembic
# Edit alembic/env.py to import Base from app.core.database
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## Role & Permission Matrix

| Endpoint | Public | Buyer | Seller | Admin |
|---|:---:|:---:|:---:|:---:|
| `GET /products` | ✅ | ✅ | ✅ | ✅ |
| `GET /products/{id}` | ✅ | ✅ | ✅ | ✅ |
| `POST /products` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /products/{id}` | ❌ | ❌ | ✅ (own) | ✅ |
| `DELETE /products/{id}` | ❌ | ❌ | ✅ (own) | ✅ |
| `GET /cart` | ❌ | ✅ | ✅ | ✅ |
| `POST /cart/items` | ❌ | ✅ | ✅ | ✅ |
| `POST /checkout` | ❌ | ✅ | ✅ | ✅ |
| `GET /orders` | ❌ | ✅ (own) | ✅ (own) | ✅ |
| `GET /admin/users` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /admin/orders/{id}/status` | ❌ | ❌ | ❌ | ✅ |
| `POST /webhooks/stripe` | ✅ (signed) | - | - | - |

---

## Payment Flow (Stripe)

```
Frontend              Backend                Stripe
   |                     |                     |
   |-- POST /checkout --> |                     |
   |                     |-- Create Order      |
   |                     |-- PaymentIntent --> |
   |                     |<-- client_secret -- |
   |<-- { client_secret} |                     |
   |                     |                     |
   |-- confirmPayment() ----------------->     |
   |                     |                     |
   |                     |<-- webhook event -- |
   |                     |   payment_intent.   |
   |                     |   succeeded         |
   |                     |-- Order → PAID      |
```

### Setting up Stripe Webhook
1. Install Stripe CLI: `stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe`
2. Copy the webhook signing secret → `STRIPE_WEBHOOK_SECRET` in `.env`
3. In production, register `https://yourdomain.com/api/v1/webhooks/stripe` in the Stripe Dashboard

---

## Security Features

- **Argon2** password hashing (memory-hard, best-in-class)
- **JWT** with separate short-lived access tokens (30 min) and refresh tokens (7 days)
- **RBAC** — every endpoint declares its required role via FastAPI `Depends`
- **Rate limiting** middleware (100 req/min per IP; swap for Redis in production)
- **Soft deletes** — products are deactivated, not destroyed
- **Stock validation** at cart-add and checkout time
- **Stripe signature verification** on webhook events
- Swagger UI hidden in production (`DEBUG=False`)