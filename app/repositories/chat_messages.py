# app/repositories/chat_messages.py
"""
Репозиторий для работы с сообщениями чата в базе данных.
Только операции доступа к данным — без бизнес-логики и внешних вызовов.
"""

from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ChatMessage


class ChatMessageRepository:
    """
    Репозиторий для CRUD-операций с сообщениями чата.
    Отвечает только за доступ к данным в БД.
    Не содержит бизнес-логики, не обращается к OpenRouter,
    не решает какие сообщения включать в контекст.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория.
        Args:
            session: Асинхронная сессия SQLAlchemy для работы с БД.
        """
        self._session: AsyncSession = session

    async def create(
        self,
        user_id: int,
        role: str,
        content: str,
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> ChatMessage:
        """
        Создать новое сообщение в базе данных.

        Args:
            user_id: ID пользователя, отправившего сообщение.
            role: Роль отправителя ('user' или 'assistant').
            content: Текст сообщения.
            model: Название модели LLM (для сообщений assistant, опционально).
            tokens_used: Количество использованных токенов (опционально).
        Returns:
            Созданный объект ChatMessage с заполненным id и created_at.
        Note:
            Метод делает commit и refresh для получения актуальных данных.
        """
        message = ChatMessage(
            user_id=user_id,
            role=role,
            content=content,
            model=model,
            tokens_used=tokens_used,
        )

        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)

        return message

    async def get_last_n(
        self,
        user_id: int,
        limit: int = 10,
    ) -> List[ChatMessage]:
        """
        Получить последние N сообщений пользователя.
        Args:
            user_id: ID пользователя, чьи сообщения нужно получить.
            limit: Максимальное количество сообщений для возврата.
        Returns:
            Список сообщений, отсортированных по дате создания (возрастание).
        Note:
            Сообщения возвращаются в хронологическом порядке (старые → новые).
            Сортировка выполняется по created_at ASC.
        """
        query = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_last_n_desc(
        self,
        user_id: int,
        limit: int = 10,
    ) -> List[ChatMessage]:
        """
        Получить последние N сообщений пользователя (в обратном порядке).
        Args:
            user_id: ID пользователя, чьи сообщения нужно получить.
            limit: Максимальное количество сообщений для возврата.
        Returns:
            Список сообщений, отсортированных по дате создания (убывание).
        Note:
            Сообщения возвращаются в обратном хронологическом порядке (новые → старые).
            Удобно для отображения в UI.
        """
        query = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def delete_all_by_user(self, user_id: int) -> int:
        """
        Удалить всю историю сообщений пользователя.
        Args:
            user_id: ID пользователя, чьи сообщения нужно удалить.

        Returns:
            Количество удалённых сообщений.
        Note:
            Используется массовое удаление для производительности.
            Каскадное удаление через relationship также работает, но этот метод
            даёт явный контроль и возвращает количество удалённых записей.
        """
        query = delete(ChatMessage).where(ChatMessage.user_id == user_id)
        result = await self._session.execute(query)
        await self._session.commit()

        return result.rowcount or 0

    async def count_by_user(self, user_id: int) -> int:
        """
        Подсчитать количество сообщений пользователя.
        Args:
            user_id: ID пользователя.
        Returns:
            Количество сообщений в истории пользователя.
        """
        from sqlalchemy import func

        query = select(func.count(ChatMessage.id)).where(ChatMessage.user_id == user_id)
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def get_by_id(
        self, message_id: int, user_id: Optional[int] = None
    ) -> Optional[ChatMessage]:
        """
        Получить сообщение по ID.
        Args:
            message_id: ID сообщения.
            user_id: Опционально ID пользователя для проверки принадлежности.
        Returns:
            Объект ChatMessage если найден, иначе None.
        """
        query = select(ChatMessage).where(ChatMessage.id == message_id)

        if user_id is not None:
            query = query.where(ChatMessage.user_id == user_id)

        result = await self._session.execute(query)
        return result.scalar_one_or_none()
