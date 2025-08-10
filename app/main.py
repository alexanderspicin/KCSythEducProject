import uvicorn
from fastapi import FastAPI

from routes import router
from database.init_exchange_service import init_database
from logger_config import setup_logging, get_logger

#Создаем директорию для хранения генерации
from pathlib import Path

# Create single directory
Path("output").mkdir(exist_ok=True)

# Настраиваем логирование при старте модуля
setup_logging(log_level="INFO", log_to_file=True)
logger = get_logger(__name__)

app = FastAPI()
# Инициализируем базу данных и ExchangeService при запуске
@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI application")
    init_database()
    logger.info("Application startup completed")

app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="debug"
    )
