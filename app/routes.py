from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.schema import CreateUserSchema, UserSchema, Token, TransactionSchema, CreateTransactionSchema
from database.dependency import get_db
from services.auth_service import verify_password, create_access_token, get_current_user
from services.transaction_service import create_transaction, process_transaction
from services.user_service import create_user
from logger_config import get_logger
from database.models import Users
router = APIRouter()
logger = get_logger(__name__)


@router.post('/login', response_model=Token)
def login(user_details: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == user_details.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Incorrect username or password")
    if not verify_password(user_details.password, user.password):
        raise HTTPException(status_code=404, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


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


@router.get("/protected-route")
async def protected_route(current_user: Users = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}"}


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: Users = Depends(get_current_user)):
    return current_user


@router.get("/credit", response_model=TransactionSchema)
def create_credit(amount: float, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    try:
        transaction_schema = CreateTransactionSchema(user_id=current_user.id, transaction_type='CREDIT',amount=amount)
        db_transaction = create_transaction(transaction_schema, db=db)
        process_transaction(db_transaction.id, db=db)
        return db_transaction
    except Exception as e:
        logger.error(f"Credit API request failed for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

