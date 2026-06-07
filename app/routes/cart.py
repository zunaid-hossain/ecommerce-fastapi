from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cart import CartItem
from app.models.interaction import UserInteraction
from app.models.product import Product
from app.models.user import User

router = APIRouter()


class CartItemCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


@router.get("/")
def get_cart(user_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(CartItem).filter(CartItem.user_id == user_id).all()


@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_item(payload: CartItemCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if payload.quantity < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be at least 1")

    item = db.query(CartItem).filter(
        CartItem.user_id == payload.user_id,
        CartItem.product_id == payload.product_id,
    ).first()
    if item:
        item.quantity += payload.quantity
    else:
        item = CartItem(**payload.model_dump())
        db.add(item)

    db.add(UserInteraction(
        user_id=payload.user_id,
        product_id=payload.product_id,
        interaction_type="add_to_cart",
    ))
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}")
def update_item(item_id: int, payload: CartItemUpdate, db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    if payload.quantity < 1:
        db.delete(item)
        db.commit()
        return {"status": "removed"}
    item.quantity = payload.quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}
