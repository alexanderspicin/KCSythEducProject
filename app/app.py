import uvicorn
from fastapi import FastAPI

from routes import router
from database.database import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == '__main__':
    uvicorn.run(
        'app:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="debug"
    )
