# app/usecases/chat.py
"""
Бизнес-логика общения с LLM.
Только доменные правила — без HTTP, FastAPI и прямых зависимостей от БД.
"""

from typing import Optional

from app.repositories.chat_messages import ChatMessageRepository
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageHistory
from app.services.openrouter_client import OpenRouterService


class ChatUsecase:
    """
    Use case для общения с языковой моделью.

    Отвечает за бизнес-логику формирования контекста,
    сохранения истории и взаимодействия с OpenRouter.
    Не зависит от FastAPI, работает только с доменными ошибками.
    """

    # Системные роли для LLM API
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    def __init__(
        self,
        message_repo: ChatMessageRepository,
        openrouter_service: OpenRouterService,
    ) -> None:
        """
        Инициализация usecase.

        Args:
            message_repo: Репозиторий для работы с сообщениями.
            openrouter_service: Клиент для вызова OpenRouter API.
        """
        self._message_repo = message_repo
        self._openrouter_service = openrouter_service

    async def ask(
        self,
        user_id: int,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Обработать запрос пользователя к LLM.

        Бизнес-правила:
            1. Сохранить запрос пользователя в историю
            2. Сформировать контекст для модели (system + history + prompt)
            3. Вызвать внешнюю LLM (OpenRouter)
            4. Сохранить ответ модели в историю
            5. Вернуть ответ клиенту

        Args:
            user_id: ID текущего пользователя.
            request: Данные запроса из API (prompt, system, max_history, temperature).

        Returns:
            Ответ от модели с текстом и метаданными.

        Raises:
            ExternalServiceError: Если OpenRouter вернул ошибку.
            NotFoundError: Если пользователь не найден (опционально).
        """
        # Модель из .env — игнорируем любые попытки переопределения
        # target_model = settings.openrouter_model

        # ==================== 1. Сохраняем запрос пользователя ====================
        await self._message_repo.create(
            user_id=user_id,
            role=self.ROLE_USER,
            content=request.prompt,
        )

        # ==================== 2. Формируем контекст для LLM ====================
        messages = await self._build_context(
            user_id=user_id,
            system_instruction=request.system,
            max_history=request.max_history,
            current_prompt=request.prompt,
        )

        # ==================== 3. Вызываем OpenRouter ====================
        llm_response = await self._openrouter_service.generate(
            messages=messages,
            temperature=request.temperature,
            # model=target_model,
        )

        # ==================== 4. Сохраняем ответ ассистента ====================
        await self._message_repo.create(
            user_id=user_id,
            role=self.ROLE_ASSISTANT,
            content=llm_response.answer,
            model=llm_response.model,
            tokens_used=llm_response.tokens_used,
        )

        # ==================== 5. Возвращаем ответ ====================
        return ChatResponse(
            answer=llm_response.answer,
            model=llm_response.model,
            tokens_used=llm_response.tokens_used,
            finish_reason=llm_response.finish_reason,
        )

    async def _build_context(
        self,
        user_id: int,
        system_instruction: Optional[str],
        max_history: int,
        current_prompt: str,
    ) -> list[dict[str, str]]:
        """
        Сформировать список сообщений для отправки в LLM.

        Порядок сообщений:
            1. System (если есть) — инструкция для модели
            2. History — предыдущие сообщения пользователя (chronological order)
            3. Current prompt — текущий запрос

        Args:
            user_id: ID пользователя для загрузки истории.
            system_instruction: Системная инструкция (опционально).
            max_history: Сколько последних сообщений истории включить.
            current_prompt: Текущий запрос пользователя.

        Returns:
            Список сообщений в формате OpenRouter API.
        """
        messages: list[dict[str, str]] = []

        # 1. Добавляем системную инструкцию (если есть)
        if system_instruction:
            messages.append(
                {
                    "role": self.ROLE_SYSTEM,
                    "content": system_instruction,
                }
            )

        # 2. Получаем историю из репозитория
        # max_history — это количество сообщений истории (не включая текущий prompt)
        history = await self._message_repo.get_last_n(
            user_id=user_id,
            limit=max_history,
        )

        # 3. Конвертируем ORM-объекты в формат LLM API
        for msg in history:
            messages.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                }
            )

        # 4. Добавляем текущий запрос пользователя
        messages.append(
            {
                "role": self.ROLE_USER,
                "content": current_prompt,
            }
        )

        return messages

    async def get_conversation_history(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[ChatMessageHistory]:
        """
        Получить историю переписки пользователя.

        Args:
            user_id: ID пользователя.
            limit: Максимальное количество сообщений для возврата.

        Returns:
            Список сообщений истории.
        """
        messages = await self._message_repo.get_last_n(
            user_id=user_id,
            limit=limit,
        )

        return [
            ChatMessageHistory(role=msg.role, content=msg.content) for msg in messages
        ]

    async def clear_conversation_history(self, user_id: int) -> int:
        """
        Очистить всю историю переписки пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Количество удалённых сообщений.
        """
        deleted_count = await self._message_repo.delete_all_by_user(user_id=user_id)
        return deleted_count
