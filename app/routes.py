import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from database.schema import CreateUserSchema, UserSchema, Token, TransactionSchema, CreateTransactionSchema, \
    GenerationHistorySchema, CreateGenerationSchema
from database.dependency import get_db

from services.auth_service import verify_password, create_access_token, get_current_user
from services.transaction_service import create_transaction, process_transaction
from services.tts_service import count_tokens, create_prediction
from services.user_service import create_user
from logger_config import get_logger
from database.models import Users, GenerationHistory, Balance

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


@router.post("/register", response_model=UserSchema)
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
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
        transaction_schema = CreateTransactionSchema(user_id=current_user.id, transaction_type='CREDIT', amount=amount)
        db_transaction = create_transaction(transaction_schema, db=db)
        process_transaction(db_transaction.id, db=db)
        return db_transaction
    except Exception as e:
        logger.error(f"Credit API request failed for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/predictions', response_model=List[GenerationHistorySchema])
def predictions_list(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    db_generation_history = db.query(GenerationHistory).filter(GenerationHistory.user_id == current_user.id).all()
    if not db_generation_history:
        raise HTTPException(status_code=404, detail="No generation history")

    # Use from_orm for each instance
    generation_history_schema = [GenerationHistorySchema.from_orm(data) for data in db_generation_history]
    return generation_history_schema


@router.post('/predict', response_model=GenerationHistorySchema)
def create_generation(text: str, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    """Создание задачи на генерацию (асинхронно)"""
    tokens_spent = count_tokens(text)
    user_balance = db.query(Balance).filter(Balance.user_id == current_user.id).first()

    if user_balance.amount < tokens_spent:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    try:
        # Создаем и отправляем задачу в очередь (асинхронно)
        prediction = create_prediction(
            tokens_spent=tokens_spent,
            generation_data=CreateGenerationSchema(text=text),
            db=db,
            user_id=current_user.id
        )
        return prediction

    except Exception as e:
        logger.error(f"Prediction API request failed for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/predictions/{generation_id}/status')
def get_generation_status(
        generation_id: str,
        current_user: Users = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Проверка статуса генерации"""
    from services.tts_service import check_generation_status

    status = check_generation_status(generation_id, current_user.id, db)

    if not status:
        raise HTTPException(
            status_code=404,
            detail="Generation not found or access denied"
        )

    return status


@router.get('/predictions/{generation_id}/audio')
def get_audio_by_id(
        generation_id: str,
        current_user: Users = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    generation = db.query(GenerationHistory).filter(
        GenerationHistory.id == generation_id,
        GenerationHistory.user_id == current_user.id
    ).first()

    if not generation:
        raise HTTPException(
            status_code=404,
            detail="Generation not found or access denied"
        )

    from database.enums import Status
    if generation.status != Status.DONE:
        return {
            "status": generation.status.value,
            "message": "Audio is not ready yet. Please check status endpoint."
        }

    file_path = generation.s3_link
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Audio file not found on server"
        )

    return FileResponse(
        path=file_path,
        media_type='audio/wav',
        filename=f"generation_{generation_id}.wav"
    )
