# app/api/deps.py
"""
Dependency Injection для API слоя.
Предоставляет сессии БД, репозитории, usecase-объекты и аутентификацию.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_async_session
from app.repositories.users import UserRepository
from app.repositories.chat_messages import ChatMessageRepository
from app.services.openrouter_client import OpenRouterService
from app.usecases.auth import AuthUsecase
from app.usecases.chat import ChatUsecase

# ==================== OAuth2 SCHEME ====================
# URL для кнопки "Authorize" в Swagger UI
# Должен совпадать с эндпоинтом логина
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ==================== DATABASE SESSION ====================


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет асинхронную сессию базы данных.
    Используется как зависимость для репозиториев.
    Сессия автоматически закрывается после запроса.
    Yields:
        AsyncSession: Сессия SQLAlchemy для работы с БД.
    """
    async for session in get_async_session():
        yield session


# ==================== REPOSITORIES ====================


def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """
    Создаёт и возвращает UserRepository.
    Args:
        session: Сессия БД из зависимости get_session.
    Returns:
        UserRepository: Репозиторий для работы с пользователями.
    """
    return UserRepository(session=session)


def get_chat_message_repo(
    session: AsyncSession = Depends(get_session),
) -> ChatMessageRepository:
    """
    Создаёт и возвращает ChatMessageRepository.
    Args:
        session: Сессия БД из зависимости get_session.
    Returns:
        ChatMessageRepository: Репозиторий для работы с сообщениями.
    """
    return ChatMessageRepository(session=session)


# ==================== SERVICES ====================


def get_openrouter_service() -> OpenRouterService:
    """
    Создаёт и возвращает OpenRouterService.

    Returns:
        OpenRouterService: Клиент для вызова OpenRouter API.
    """
    return OpenRouterService(
        api_key=settings.openrouter_api_key,
        default_model=settings.openrouter_model,  # ✅ Модель из .env
    )


# ==================== USECASES ====================


def get_auth_usecase(user_repo: UserRepository = Depends(get_user_repo)) -> AuthUsecase:
    """
    Создаёт и возвращает AuthUsecase.

    Args:
        user_repo: UserRepository из зависимости.

    Returns:
        AuthUsecase: Use case для аутентификации.
    """
    return AuthUsecase(user_repo=user_repo)


def get_chat_usecase(
    message_repo: ChatMessageRepository = Depends(get_chat_message_repo),
    openrouter_service: OpenRouterService = Depends(get_openrouter_service),
) -> ChatUsecase:
    """
    Создаёт и возвращает ChatUsecase.

    Args:
        message_repo: ChatMessageRepository из зависимости.
        openrouter_service: OpenRouterService из зависимости.

    Returns:
        ChatUsecase: Use case для общения с LLM.
    """
    return ChatUsecase(
        message_repo=message_repo,
        openrouter_service=openrouter_service,
    )


# ==================== AUTHENTICATION ====================


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    Извлекает user_id из JWT-токена.
    Используется как зависимость для защищённых эндпоинтов.
    Автоматически возвращает 401 если токен недействителен.
    Args:
        token: JWT-токен из заголовка Authorization: Bearer <token>.
    Returns:
        int: ID текущего пользователя.
    Raises:
        HTTPException: 401 если токен недействителен или истёк.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "UNAUTHORIZED",
            "message": "Недействительный токен доступа",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем JWT-токен
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])

        # Извлекаем user_id из claims
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return int(user_id)

    except JWTError:
        raise credentials_exception


async def get_current_user_id_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[int]:
    """
    Извлекает user_id из JWT-токена (опционально).
    Используется для эндпоинтов, где аутентификация не обязательна.
    Возвращает None если токен не предоставлен или недействителен.
    Args:
        token: JWT-токен из заголовка Authorization (опционально).
    Returns:
        Optional[int]: ID пользователя или None.
    """
    try:
        if token is None:
            return None

        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None

        return int(user_id)

    except JWTError:
        return None


# ==================== COMBINED DEPENDENCIES ====================


async def get_auth_dependencies(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Предоставляет все зависимости для auth-эндпоинтов.
    Удобно для тестирования или когда нужно несколько зависимостей сразу.
    Returns:
        dict: Словарь с готовыми объектами (repo, usecase).
    """
    user_repo = UserRepository(session=session)
    auth_usecase = AuthUsecase(user_repo=user_repo)

    return {
        "session": session,
        "user_repo": user_repo,
        "auth_usecase": auth_usecase,
    }


async def get_chat_dependencies(
    session: AsyncSession = Depends(get_session),
    openrouter_service: OpenRouterService = Depends(get_openrouter_service),
) -> dict:
    """
    Предоставляет все зависимости для chat-эндпоинтов.
    Returns:
        dict: Словарь с готовыми объектами (repo, usecase, service).
    """
    message_repo = ChatMessageRepository(session=session)
    chat_usecase = ChatUsecase(
        message_repo=message_repo,
        openrouter_service=openrouter_service,
    )

    return {
        "session": session,
        "message_repo": message_repo,
        "openrouter_service": openrouter_service,
        "chat_usecase": chat_usecase,
    }
