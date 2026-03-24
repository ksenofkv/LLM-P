# app/main.py
# =============================================================================
# ТОЧКА ВХОДА ПРИЛОЖЕНИЯ
# Здесь собирается FastAPI-приложение, подключаются роутеры и инфраструктура.
# Нет бизнес-логики, нет работы с репозиториями — только конфигурация.
# =============================================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api import routes_auth, routes_chat


# =============================================================================
# СОБЫТИЯ ЖИЗНЕННОГО ЦИКЛА ПРИЛОЖЕНИЯ
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения (startup / shutdown).
    
    Вызывается автоматически при старте и остановке сервера.
    """
    
    # --- СТАРТ ПРИЛОЖЕНИЯ ---
    async with engine.begin() as conn:
        # Создаём все таблицы БД, если их нет
        # Base.metadata содержит информацию о всех ORM-моделях
        await conn.run_sync(Base.metadata.create_all)
    
    # Логирование старта (опционально)
    print(f"✅ Database initialized: {settings.sqlite_path}")
    print(f"✅ App started in {settings.env} mode")
    
    yield  # Приложение работает здесь
    
    # --- ОСТАНОВКА ПРИЛОЖЕНИЯ ---
    # Здесь можно закрыть соединения, очистить кэш и т.д.
    await engine.dispose()
    print("✅ Database connections closed")


# =============================================================================
# ФУНКЦИЯ СОЗДАНИЯ ПРИЛОЖЕНИЯ
# =============================================================================

def create_app() -> FastAPI:
    """
    Фабричная функция для создания и настройки FastAPI-приложения.
    
    Возвращает полностью настроенный объект app со всеми middleware и роутерами.
    """
    
    # 1. Создаём экземпляр приложения
    application = FastAPI(
        title=settings.app_name,
        description="FastAPI service with JWT auth, SQLite, and OpenRouter LLM proxy",
        version="0.1.0",
        lifespan=lifespan,  # Подключаем обработчик событий старта/остановки
    )
    
    # 2. Настраиваем CORS (Cross-Origin Resource Sharing)
    # Разрешает запросы с других доменов (например, с фронтенда)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене заменить на конкретные домены!
        allow_credentials=True,
        allow_methods=["*"],  # Разрешаем все HTTP-методы (GET, POST, PUT, DELETE...)
        allow_headers=["*"],  # Разрешаем все заголовки
    )
    
    # 3. Подключаем роутеры (API-эндпоинты)
    # Все маршруты из этих модулей станут доступны в приложении
    application.include_router(routes_auth.router)  # /auth/*
    application.include_router(routes_chat.router)  # /chat/*
    
    # 4. Добавляем технический эндпоинт для проверки здоровья
    @application.get("/health", tags=["health"])
    def health_check():
        """
        Технический эндпоинт для мониторинга.
        
        Возвращает статус приложения и текущее окружение.
        Используется для проверки, что сервер запущен и отвечает.
        """
        return {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.env,
        }
    
    return application


# =============================================================================
# ТОЧКА ВХОДА ДЛЯ UVICORN
# =============================================================================

# Создаём экземпляр приложения для запуска через uvicorn
# Команда: uv run uvicorn app.main:app --reload
app = create_app()
