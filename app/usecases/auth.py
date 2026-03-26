# app/usecases/auth.py
"""
Бизнес-логика аутентификации и авторизации.
Только доменные правила — без HTTP, FastAPI и веб-зависимостей.
"""

from typing import Optional

from app.core.errors import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.users import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.db.models import User


class AuthUsecase:
    """
    Use case для операций аутентификации.
    
    Отвечает за бизнес-логику регистрации, входа и получения профиля.
    Не зависит от FastAPI, работает только с доменными ошибками.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        """
        Инициализация usecase.
        
        Args:
            user_repo: Репозиторий для работы с пользователями.
        """
        self._user_repo = user_repo

    async def register(self, request: RegisterRequest) -> UserPublic:
        """
        Зарегистрировать нового пользователя.
        
        Бизнес-правила:
            1. Email должен быть уникальным
            2. Пароль должен быть захеширован перед сохранением
            3. Роль по умолчанию — "user"
        
        Args:
            request: Данные для регистрации из API.
            
        Returns:
            Публичные данные созданного пользователя.
            
        Raises:
            ConflictError: Если email уже занят.
        """
        # 1. Проверяем, не занят ли email
        existing_user = await self._user_repo.get_by_email(request.email)
        if existing_user is not None:
            raise ConflictError(
                message="Пользователь с таким email уже существует",
                details={"field": "email", "value": request.email},
            )
        
        # 2. Хешируем пароль (в security слое, не в репозитории)
        password_hash = hash_password(request.password)
        
        # 3. Создаём пользователя в БД
        user = await self._user_repo.create(
            email=request.email,
            password_hash=password_hash,
            role="user",
        )
        
        # 4. Возвращаем публичные данные (конвертация ORM → Pydantic)
        return UserPublic.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Аутентифицировать пользователя и выдать JWT-токен.
        
        Бизнес-правила:
            1. Пользователь должен существовать
            2. Пароль должен совпадать с хешем в БД
            3. Токен должен содержать user_id и expire
        
        Args:
            email: Email адрес пользователя.
            password: Пароль в открытом виде.
            
        Returns:
            Токен доступа (access_token + token_type).
            
        Raises:
            UnauthorizedError: Если email не найден или пароль неверный.
        """
        # 1. Ищем пользователя по email
        user = await self._user_repo.get_by_email(email)
        if user is None:
            # Не уточняем, что именно неверно (безопасность)
            raise UnauthorizedError(
                message="Неверный email или пароль",
                details={"field": "credentials"},
            )
        
        # 2. Проверяем пароль
        is_valid = verify_password(password, user.password_hash)
        if not is_valid:
            raise UnauthorizedError(
                message="Неверный email или пароль",
                details={"field": "credentials"},
            )
        
        # 3. Проверяем, активен ли аккаунт
        if not user.is_active:
            raise UnauthorizedError(
                message="Аккаунт деактивирован",
                details={"field": "is_active", "value": False},
            )
        
        # 4. Генерируем JWT-токен (через security модуль)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def get_user_profile(self, user_id: int) -> UserPublic:
        """
        Получить профиль пользователя по ID.
        
        Бизнес-правила:
            1. Пользователь должен существовать
            2. Возвращаются только публичные данные (без пароля)
        
        Args:
            user_id: Уникальный идентификатор пользователя.
            
        Returns:
            Публичные данные пользователя.
            
        Raises:
            NotFoundError: Если пользователь не найден.
        """
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(
                message="Пользователь не найден",
                details={"field": "id", "value": user_id},
            )
        
        return UserPublic.model_validate(user)

    async def get_user_by_email(self, email: str) -> UserPublic:
        """
        Получить пользователя по email (вспомогательный метод).
        
        Args:
            email: Email адрес пользователя.
            
        Returns:
            Публичные данные пользователя.
            
        Raises:
            NotFoundError: Если пользователь не найден.
        """
        user = await self._user_repo.get_by_email(email)
        if user is None:
            raise NotFoundError(
                message="Пользователь не найден",
                details={"field": "email", "value": email},
            )
        
        return UserPublic.model_validate(user)