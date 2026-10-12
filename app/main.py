from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.routers.auth import router as auth_router
from app.routers.registration import router as registration_router
from app.routers.books import router as books_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router
from app.routers.rentals import router as rentals_router
from app.routers.reviews import router as reviews_router
from app.routers.authors import router as authors_router
from app.routers.categories import router as categories_router
from app.routers.tickets import router as tickets_router
from app.routers import admin_tickets, super_admin_tickets
from app.routers import super_admin_users
from app.routers import super_admin_employees
from app.routers import super_admin_books
from app.routers import super_admin_categories
from app.routers import super_admin_inventory
from app.routers import super_admin_orders

app = FastAPI(
    title="GyanPustak API",
    description="Backend API for GyanPustak",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(registration_router)

app.include_router(books_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(rentals_router)
app.include_router(reviews_router)
app.include_router(authors_router)
app.include_router(categories_router)

app.include_router(tickets_router)
app.include_router(admin_tickets.router)
app.include_router(super_admin_tickets.router)
app.include_router(super_admin_users.router)
app.include_router(super_admin_employees.router)
app.include_router(super_admin_books.router)
app.include_router(super_admin_categories.router)
app.include_router(super_admin_inventory.router)
app.include_router(super_admin_orders.router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "GyanPustak API",
    }


@app.get("/health/database")
def database_health(
    db: Session = Depends(get_db),
):
    result = db.execute(text("SELECT 1"))

    return {
        "database": "connected",
        "result": result.scalar(),
    }