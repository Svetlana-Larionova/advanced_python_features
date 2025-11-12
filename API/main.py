"""
FastAPI приложение
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes import sellers

logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="Woysa Club API",
    description="API для работы с данными Woysa Club",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(sellers.router)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Добро пожаловать в Woysa Club API!",
        "version": "1.0.0",
        "endpoints": {
            "sellers": {
                "get_all": "/sallers/",
                "get_by_id": "/sallers/{id}/",
                "update": "/sallers/{id}/update"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy", "service": "woysa-api"}

@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""
    logger.info("🚀 FastAPI приложение запущено")

@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке приложения"""
    logger.info("🛑 FastAPI приложение остановлено")