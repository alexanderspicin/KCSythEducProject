from fastapi import APIRouter

from database.dependency import db_dependency
from database.models import Users

router = APIRouter()

@router.get("/users/")
def get_users(db: db_dependency):  # ✅ Правильное использование
    users = db.query(Users).all()
    return users