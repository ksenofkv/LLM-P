# app/api/routes_chat.py
"""
HTTP-эндпоинты для общения с LLM.
Тонкий API слой — только вызовы usecase и обработка ошибок.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_chat_usecase, get_current_user_id
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageHistory
from app.usecases.chat import ChatUsecase
from app.core.errors import AppError

router = APIRouter(prefix="/chat", tags=["Chat"])


def _handle_domain_error(error: AppError) -> HTTPException:
    """
    Конвертирует доменные исключения в HTTPException для FastAPI.
    Args:
        error: Доменное исключение из usecase.
    Returns:
        HTTPException: Исключение с правильным статус-кодом.
    """
    return HTTPException(
        status_code=error.status_code,
        detail={
            "error": error.error_code,
            "message": error.message,
            "details": error.details,
        },
    )


@router.post(
    "/completions",
    response_model=ChatResponse,
    summary="Отправить сообщение в чат с LLM",
    description="Отправляет запрос к языковой модели и возвращает ответ. Требуется авторизация.",
    responses={
        200: {"description": "Ответ успешно получен", "model": ChatResponse},
        401: {"description": "Токен недействителен или отсутствует", "model": dict},
        502: {"description": "Ошибка внешнего сервиса (OpenRouter)", "model": dict},
    },
)
async def chat_completion(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    usecase: ChatUsecase = Depends(get_chat_usecase),
) -> ChatResponse:
    """
    Отправить сообщение в чат и получить ответ от LLM.
    **Параметры запроса:**
    - **prompt**: Текст запроса к модели (обязательно)
    - **system**: Системная инструкция для модели (опционально)
    - **max_history**: Количество сообщений истории для контекста (по умолчанию 10)
    - **temperature**: Креативность модели от 0.0 до 2.0 (по умолчанию 0.7)
    - **model**: Идентификатор модели (опционально, используется модель по умолчанию)
    **Требуется авторизация:**
    Передайте JWT-токен в заголовке: `Authorization: Bearer <token>`
    Возвращает:
    - **answer**: Текст ответа от модели
    - **model**: Использованная модель
    - **tokens_used**: Количество использованных токенов
    - **finish_reason**: Причина завершения генерации
    """
    try:
        response = await usecase.ask(user_id=user_id, request=request)
        return response
    except AppError as e:
        raise _handle_domain_error(e)


@router.get(
    "/history",
    response_model=list[ChatMessageHistory],
    summary="Получить историю переписки",
    description="Возвращает историю сообщений текущего пользователя. Требуется авторизация.",
    responses={
        200: {
            "description": "История успешно получена",
            "model": list[ChatMessageHistory],
        },
        401: {"description": "Токен недействителен или отсутствует", "model": dict},
    },
)
async def get_chat_history(
    user_id: int = Depends(get_current_user_id),
    usecase: ChatUsecase = Depends(get_chat_usecase),
    limit: int = 50,
) -> list[ChatMessageHistory]:
    """
    Получить историю переписки текущего пользователя.
    **Параметры:**
    - **limit**: Максимальное количество сообщений для возврата (по умолчанию 50)
    **Требуется авторизация:**
    Передайте JWT-токен в заголовке: `Authorization: Bearer <token>`
    Возвращает список сообщений в хронологическом порядке:
    - **role**: Роль отправителя ('user' или 'assistant')
    - **content**: Текст сообщения
    """
    try:
        history = await usecase.get_conversation_history(user_id=user_id, limit=limit)
        return history
    except AppError as e:
        raise _handle_domain_error(e)


@router.delete(
    "/history",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Очистить историю переписки",
    description="Удаляет всю историю сообщений текущего пользователя. Требуется авторизация.",
    responses={
        204: {"description": "История успешно очищена"},
        401: {"description": "Токен недействителен или отсутствует", "model": dict},
    },
)
async def clear_chat_history(
    user_id: int = Depends(get_current_user_id),
    usecase: ChatUsecase = Depends(get_chat_usecase),
) -> None:
    """
    Очистить всю историю переписки текущего пользователя.
    **Требуется авторизация:**
    Передайте JWT-токен в заголовке: `Authorization: Bearer <token>`
    **Внимание:** Это действие необратимо!
    Возвращает:
    - 204: История успешно удалена
    """
    try:
        await usecase.clear_conversation_history(user_id=user_id)
    except AppError as e:
        raise _handle_domain_error(e)
