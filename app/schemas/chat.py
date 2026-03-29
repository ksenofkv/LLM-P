# app/schemas/chat.py
"""
Pydantic-схемы для чата с LLM.
Только валидация и сериализация — без бизнес-логики.
"""

from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    """
    Запрос к чату с LLM.
    Используется в эндпоинте POST /chat/completions
    """

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Основной текст запроса к модели",
        examples=["Объясни квантовую запутанность простыми словами"],
    )
    system: str | None = Field(
        None,
        max_length=2000,
        description="Системная инструкция для модели (опционально)",
        examples=["Ты полезный ассистент, отвечающий кратко и по делу"],
    )
    max_history: int = Field(
        10,
        ge=0,
        le=100,
        description="Количество сообщений истории для контекста (0 = без истории)",
        examples=[10],
    )
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Креативность модели (0 = детерминировано, 2 = максимально креативно)",
        examples=[0.7],
    )
    # model: str | None = Field(
    # None,
    # max_length=100,
    # description="Идентификатор модели (опционально, используется модель по умолчанию)",
    # examples=["gpt-4", "llama-3"]
    # )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "Объясни квантовую запутанность простыми словами",
                "system": "Ты полезный ассистент, отвечающий кратко и по делу",
                "max_history": 10,
                "temperature": 0.7,
                # "model": "gpt-4"
            }
        }
    )


class ChatResponse(BaseModel):
    """
    Ответ от чата с LLM.
        Используется в эндпоинте POST /chat/completions
    """

    answer: str = Field(
        ...,
        description="Текст ответа от модели",
        examples=["Квантовая запутанность — это явление, при котором две частицы..."],
    )
    model: str = Field(
        ...,
        description="Идентификатор модели, которая сгенерировала ответ",
        examples=["gpt-4"],
    )
    tokens_used: int | None = Field(
        None,
        description="Количество использованных токенов (prompt + completion)",
        examples=[150],
    )
    finish_reason: str | None = Field(
        None,
        description="Причина завершения генерации (stop, length, error)",
        examples=["stop"],
    )
    conversation_id: str | None = Field(
        None,
        description="Идентификатор диалога для продолжения истории (опционально)",
        examples=["conv_12345"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Квантовая запутанность — это явление, при котором две частицы становятся взаимосвязанными...",
                # "model": "gpt-4",
                "tokens_used": 150,
                "finish_reason": "stop",
                "conversation_id": "conv_12345",
            }
        }
    )


class ChatMessageHistory(BaseModel):
    """
    Схема отдельного сообщения в истории чата.
    Используется внутри usecase для формирования контекста.
    """

    role: str = Field(
        ...,
        description="Роль отправителя: 'user' или 'assistant'",
        examples=["user", "assistant"],
    )
    content: str = Field(
        ..., description="Текст сообщения", examples=["Привет! Как дела?"]
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"role": "user", "content": "Привет! Как дела?"}}
    )
