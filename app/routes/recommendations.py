from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.recommendations.engine import HybridRecommendationEngine

router = APIRouter()


class InteractionCreate(BaseModel):
    user_id: int
    product_id: int
    interaction_type: str
    rating: float | None = None


def ensure_demo_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user

    user = User(
        id=user_id,
        email=f"demo-user-{user_id}@smart-store.local",
        username=f"demo_user_{user_id}",
        full_name="Demo Shopper",
        hashed_password=User.get_password_hash("demo-password"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/personalized")
def personalized_recommendations(
    user_id: int,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    ensure_demo_user(db, user_id)
    engine = HybridRecommendationEngine(db)
    return engine.get_personalized_recommendations(user_id=user_id, limit=limit)


@router.get("/trending")
def trending_recommendations(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    engine = HybridRecommendationEngine(db)
    return engine._get_trending_products(limit=limit)


@router.get("/similar/{product_id}")
def similar_recommendations(
    product_id: int,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    engine = HybridRecommendationEngine(db)
    return engine.get_similar_products(product_id=product_id, limit=limit)


@router.post("/record-interaction", status_code=status.HTTP_201_CREATED)
def record_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    allowed_types = {"view", "add_to_cart", "purchase", "review"}
    if payload.interaction_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interaction type",
        )

    user = ensure_demo_user(db, payload.user_id)
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    engine = HybridRecommendationEngine(db)
    engine.record_interaction(
        user_id=payload.user_id,
        product_id=payload.product_id,
        interaction_type=payload.interaction_type,
        rating=payload.rating,
    )
    return {"status": "recorded"}
