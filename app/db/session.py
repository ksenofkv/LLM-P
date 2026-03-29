# app/db/session.py
"""
Настройка асинхронной сессии SQLAlchemy для работы с БД.
Предоставляет фабрику сессий и dependency для FastAPI.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base  # noqa: F401 (импортируем для регистрации моделей)
from app.db.models import User, ChatMessage  # noqa: F401 (импортируем модели для metadata)


# -----------------------------------------------------------------------------
# Создание асинхронного engine
# -----------------------------------------------------------------------------

engine = create_async_engine(
    settings.sqlite_path,
    echo=settings.debug,  # Логировать SQL-запросы в режиме отладки
    future=True,
    pool_pre_ping=True,  # Проверять соединение перед использованием
)


# -----------------------------------------------------------------------------
# Фабрика сессий
# -----------------------------------------------------------------------------

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Не обновлять объекты после коммита (избегаем проблем с async)
    autocommit=False,
    autoflush=False,
)


# -----------------------------------------------------------------------------
# Dependency для FastAPI
# -----------------------------------------------------------------------------


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор асинхронных сессий для Dependency Injection.

    Yields:
        AsyncSession: Сессия для работы с БД.

    Note:
        - Сессия автоматически закрывается после завершения запроса
        - При ошибке происходит rollback
        - При успехе — commit
    """
    session = async_session_maker()
    try:
        yield session
        await session.commit()  # Авто-коммит при успешном выполнении
    except Exception:
        await session.rollback()  # Откат при любой ошибке
        raise
    finally:
        await session.close()  # Всегда закрываем сессию


# -----------------------------------------------------------------------------
# Утилиты для работы с БД
# -----------------------------------------------------------------------------


async def create_db_tables() -> None:
    """
    Создать все таблицы в БД на основе моделей (для разработки).

    Note:
        В продакшене используйте Alembic для миграций.
        Эта функция удобна для быстрого старта и тестирования.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db_tables() -> None:
    """
    Удалить все таблицы в БД (для тестов / сброса).

    Внимание: Все данные будут безвозвратно удалены!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
