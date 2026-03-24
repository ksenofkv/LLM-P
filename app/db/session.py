# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Формируем строку подключения
DATABASE_URL = f"sqlite+aiosqlite:///{settings.sqlite_path}"

# Создаём асинхронный engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,  # Теперь это поле существует в Settings
    future=True,
)

# Создаём фабрику асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)