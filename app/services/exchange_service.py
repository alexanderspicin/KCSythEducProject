from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from logger_config import get_logger

from database.models import ExchangeService
from database.schema import ExchangeServiceSchema, UpdateExchangeRateSchema
from database.dependency import get_db

logger = get_logger(__name__)


def get_exchange_service(db: Session = Depends(get_db)) -> ExchangeServiceSchema:
    """
    Получает единственную запись ExchangeService из базы данных
    """
    logger.debug("Fetching exchange service from database")
    exchange_service = db.query(ExchangeService).first()
    if not exchange_service:
        raise HTTPException(status_code=404, detail="Exchange service not found")
    
    return ExchangeServiceSchema.model_validate(exchange_service)


def update_exchange_rate(
    rate_data: UpdateExchangeRateSchema, 
    db: Session = Depends(get_db)
) -> ExchangeServiceSchema:
    logger.info(f"Updating exchange rate to: {rate_data.rate}")
    exchange_service = db.query(ExchangeService).first()
    if not exchange_service:
        raise HTTPException(status_code=404, detail="Exchange service not found")
    
    try:
        exchange_service.rate = rate_data.rate
        exchange_service.last_update = datetime.now(tz=timezone.utc)
        db.commit()
        db.refresh(exchange_service)
        
        return ExchangeServiceSchema.model_validate(exchange_service)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating exchange rate: {str(e)}")


def convert_rub_to_tokens(amount_in_rub: float, db: Session = Depends(get_db)) -> float:
    exchange_service = db.query(ExchangeService).first()
    if not exchange_service:
        raise HTTPException(status_code=404, detail="Exchange service not found")
    
    return amount_in_rub * exchange_service.rate