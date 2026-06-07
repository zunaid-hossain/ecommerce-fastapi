from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cart import CartItem
from app.models.interaction import UserInteraction
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User

router = APIRouter()


class OrderCreate(BaseModel):
    user_id: int
    shipping_address: str
    notes: str | None = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    cart_items = db.query(CartItem).filter(CartItem.user_id == payload.user_id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total = 0.0
    order = Order(
        user_id=payload.user_id,
        total_amount=0.0,
        shipping_address=payload.shipping_address,
        notes=payload.notes,
    )
    db.add(order)
    db.flush()

    for cart_item in cart_items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            continue
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for {product.name}",
            )
        product.stock -= cart_item.quantity
        total += product.price * cart_item.quantity
        db.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            price=product.price,
        ))
        db.add(UserInteraction(
            user_id=payload.user_id,
            product_id=product.id,
            interaction_type="purchase",
        ))
        db.delete(cart_item)

    order.total_amount = total
    db.commit()
    db.refresh(order)
    return order


@router.get("/")
def list_orders(user_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
