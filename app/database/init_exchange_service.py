from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.database import SessionLocal, engine
from database.models import ExchangeService, Base
from logger_config import get_logger

logger = get_logger(__name__)


def init_database():
    """
    Создает все таблицы и инициализирует ExchangeService
    """
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Инициализируем ExchangeService
        init_exchange_service()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def init_exchange_service():
    """
    Инициализирует единственную запись ExchangeService в базе данных
    если она еще не существует
    """
    db: Session = SessionLocal()
    try:
        # Проверяем, существует ли уже запись
        existing_service = db.query(ExchangeService).first()
        
        if existing_service is None:
            # Создаем единственную запись с курсом по умолчанию 1.2
            exchange_service = ExchangeService(
                type="default",
                rate=1.2,
                last_update=datetime.now(tz=timezone.utc)
            )
            db.add(exchange_service)
            db.commit()
            logger.info("ExchangeService record initialized successfully")
        else:
            logger.info("ExchangeService record already exists")
            
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"ExchangeService already exists: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing ExchangeService: {e}")
        raise
    finally:
        db.close()