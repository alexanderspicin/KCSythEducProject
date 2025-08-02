from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.schema import CreateUserSchema, UserSchema
from database.dependency import db_dependency, get_db
from services.user_service import create_user
from logger_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/users/")
def get_users(db: db_dependency):
    users = db.query(UserSchema).all()
    return users


@router.post("/create_user", response_model=UserSchema)
async def create_users(user: CreateUserSchema, db: Session = Depends(get_db)):
    logger.info(f"API request to create user: {user.email}")
    try:
        new_user = create_user(db=db, user_data=user)
        logger.info(f"User creation API request successful for: {user.email}")
        return new_user
    except Exception as e:
        logger.error(f"User creation API request failed for {user.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
