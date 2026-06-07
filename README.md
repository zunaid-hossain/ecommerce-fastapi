# E-Commerce FastAPI Store with Hybrid Recommendation System

A complete, fast-to-deploy e-commerce platform built with FastAPI featuring a lightweight context-aware hybrid recommendation system with cold-start handling.

## Features

### Core E-Commerce
- ✅ Product catalog management
- ✅ User authentication (JWT)
- ✅ Shopping cart & order management
- ✅ Order history & tracking
- ✅ Admin dashboard endpoints

### Recommendation System
- ✅ Hybrid approach (Collaborative + Content-Based)
- ✅ Cold-start handling for new users/products
- ✅ Context-aware recommendations
- ✅ Real-time personalization
- ✅ Trending products
- ✅ Similar products

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy + PostgreSQL
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic
- **ML/Recommendations**: scikit-learn, NumPy
- **Task Queue**: Celery (optional)
- **Caching**: Redis (optional)

## Project Structure

```
ecommerce-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database setup
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── routes/                 # API endpoints
│   ├── services/               # Business logic
│   ├── recommendations/        # Recommendation engine
│   ├── middleware/             # Custom middleware
│   ├── utils/                  # Utility functions
│   └── security/               # JWT & security
├── tests/                      # Test cases
├── requirements.txt            # Dependencies
├── .env.example                # Environment variables
├── docker-compose.yml          # Docker setup
└── README.md
```

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/zunaid-hossain/ecommerce-fastapi.git
cd ecommerce-fastapi
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start the Server
```bash
uvicorn app.main:app --reload
```

API Documentation: http://localhost:8000/docs

## API Endpoints

### Products
- `GET /api/v1/products` - List products with recommendations
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/products/{id}/similar` - Get similar products
- `POST /api/v1/products` - Create product (admin)

### Users & Auth
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update profile

### Cart & Orders
- `GET /api/v1/cart` - Get shopping cart
- `POST /api/v1/cart/items` - Add item to cart
- `DELETE /api/v1/cart/items/{item_id}` - Remove item
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders` - Get user orders
- `GET /api/v1/orders/{id}` - Get order details

### Recommendations
- `GET /api/v1/recommendations/personalized` - Get personalized recommendations
- `GET /api/v1/recommendations/trending` - Get trending products
- `GET /api/v1/recommendations/similar/{product_id}` - Get similar products

## License

MIT
