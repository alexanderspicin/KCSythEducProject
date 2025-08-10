# services/tts_service.py
from fastapi import Depends
import uuid
from datetime import datetime, timezone

from database.dependency import get_db
from database.models import GenerationHistory
from database.schema import CreateGenerationSchema, GenerationHistorySchema, CreateTransactionSchema
from database.enums import Status
from sqlalchemy.orm import Session

# Импортируем только для подсчета токенов
try:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-multilingual-v1.1")
except:
    tokenizer = None

from services.transaction_service import process_transaction, create_transaction
from ml_worker.task_model import GenerationTask
from ml_worker.publisher_manager import publisher_manager
from logger_config import get_logger

logger = get_logger(__name__)


def count_tokens(text: str) -> int:
    """Count tokens for input text"""
    if tokenizer:
        tokens = tokenizer(text, return_tensors="pt")
        return tokens.input_ids.shape[1]
    else:
        # Fallback: примерный подсчет по словам
        return len(text.split()) * 2


def create_prediction(
        user_id: uuid.UUID,
        tokens_spent: int,
        generation_data: CreateGenerationSchema,
        db: Session = Depends(get_db)
) -> GenerationHistorySchema:
    """Создание задачи на генерацию и отправка в очередь"""

    transaction_schema = CreateTransactionSchema(
        user_id=user_id,
        transaction_type='DEBIT',
        amount=tokens_spent
    )
    created_transaction_schema = create_transaction(transaction_schema, db)
    process_transaction(transaction_id=created_transaction_schema.id, db=db)

    generation_id = uuid.uuid4()
    db_generation_history = GenerationHistory(
        id=generation_id,
        text=generation_data.text,
        user_id=user_id,
        tokens_spent=tokens_spent,
        status=Status.PROCESSING,  # Начальный статус
        timestamp=datetime.now(tz=timezone.utc)
    )
    db.add(db_generation_history)
    db.commit()
    db.refresh(db_generation_history)

    task = GenerationTask(
        generation_id=str(generation_id),
        user_id=str(user_id),
        text=generation_data.text,
        tokens_spent=tokens_spent
    )

    try:
        publisher = publisher_manager.get_publisher()
        success = publisher.publish_task(task)

        if success:
            logger.info(f"Task for generation {generation_id} sent to queue")
        else:
            logger.error(f"Failed to send task for generation {generation_id}")
            # Обновляем статус на FAILED
            db_generation_history.status = Status.FAILED
            db.commit()
            raise Exception("Failed to send task to queue")

    except Exception as e:
        logger.error(f"Error sending task to queue: {e}")
        db_generation_history.status = Status.FAILED
        db.commit()
        raise

    generation_schema = GenerationHistorySchema(
        id=db_generation_history.id,
        user_id=user_id,
        tokens_spent=tokens_spent,
        text=db_generation_history.text,
        timestamp=db_generation_history.timestamp,
        status=db_generation_history.status
    )

    return generation_schema


def check_generation_status(generation_id: str, user_id: str, db: Session) -> dict:
    """Проверка статуса генерации"""
    generation = db.query(GenerationHistory).filter(
        GenerationHistory.id == generation_id,
        GenerationHistory.user_id == user_id
    ).first()

    if not generation:
        return None

    return {
        "id": str(generation.id),
        "status": generation.status.value,
        "text": generation.text,
        "s3_link": generation.s3_link,
        "timestamp": generation.timestamp.isoformat(),
        "tokens_spent": generation.tokens_spent
    }
