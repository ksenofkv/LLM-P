# app/repositories/users.py
"""
Репозиторий для работы с пользователями в базе данных.
Только операции доступа к данным — без бизнес-логики, хеширования и JWT.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User


class UserRepository:
    """
    Репозиторий для CRUD-операций с пользователями.
    Отвечает только за доступ к данным в БД.
    Не содержит бизнес-логики, хеширования паролей или создания токенов.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория.
        Args:
            session: Асинхронная сессия SQLAlchemy для работы с БД.
        """
        self._session: AsyncSession = session

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Получить пользователя по email.
        Args:
            email: Email адрес пользователя.
        Returns:
            Объект User если найден, иначе None.
        """
        query = select(User).where(User.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID.
        Args:
            user_id: Уникальный идентификатор пользователя.
        Returns:
            Объект User если найден, иначе None.
        """
        query = select(User).where(User.id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        role: str = "user",
        full_name: Optional[str] = None,
    ) -> User:
        """
        Создать нового пользователя в базе данных.
        Args:
            email: Email адрес пользователя.
            password_hash: Хеш пароля (должен быть захеширован до вызова этого метода).
            role: Роль пользователя (по умолчанию "user").
            full_name: Имя пользователя (опционально).
        Returns:
            Созданный объект User с заполненным id и created_at.
        Note:
            Метод делает commit и refresh для получения актуальных данных.
        """
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
        )

        if full_name:
            # Если в модели User есть поле full_name
            # Если нет — удалите эту строку
            pass

        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)

        return user

    async def update(self, user: User, **kwargs) -> User:
        """
        Обновить данные пользователя.
        Args:
            user: Объект пользователя для обновления.
            **kwargs: Поля для обновления (например, email, role, is_active).
        Returns:
            Обновлённый объект User.
        """
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await self._session.commit()
        await self._session.refresh(user)

        return user

    async def delete(self, user: User) -> None:
        """
        Удалить пользователя из базы данных.
        Args:
            user: Объект пользователя для удаления.
        """
        await self._session.delete(user)
        await self._session.commit()

    async def exists_by_email(self, email: str) -> bool:
        """
        Проверить, существует ли пользователь с таким email.
        Args:
            email: Email адрес для проверки.
        Returns:
            True если пользователь существует, иначе False.
        """
        query = select(User.id).where(User.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none() is not None
