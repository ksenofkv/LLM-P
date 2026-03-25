# app/schemas/user.py
"""
Pydantic-схемы для пользовательских данных.
Только публичные поля — без паролей и чувствительной информации.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserPublic(BaseModel):
    """
    Публичные данные пользователя для ответов API.
    
    Не содержит паролей, хешей и другой чувствительной информации.
    Используется в эндпоинтах: GET /auth/me, POST /auth/register, и др.
    """
    id: int = Field(
        ...,
        description="Уникальный идентификатор пользователя",
        examples=[1]
    )
    email: EmailStr = Field(
        ...,
        description="Email адрес пользователя",
        examples=["user@example.com"]
    )
    role: str = Field(
        "user",
        description="Роль пользователя (user, admin, moderator)",
        examples=["user"]
    )
    is_active: bool = Field(
        True,
        description="Статус аккаунта",
        examples=[True]
    )
    created_at: str | None = Field(
        None,
        description="Дата создания аккаунта (ISO 8601)",
        examples=["2024-01-01T12:00:00Z"]
    )

    model_config = ConfigDict(
        from_attributes=True,  # Позволяет FastAPI конвертировать ORM-объекты в схему
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "role": "user",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    )


class UserUpdate(BaseModel):
    """
    Схема для обновления данных пользователя.
    
    Все поля опциональны — обновляются только переданные значения.
    """
    email: EmailStr | None = Field(
        None,
        max_length=255,
        description="Новый email адрес",
        examples=["newemail@example.com"]
    )
    full_name: str | None = Field(
        None,
        max_length=100,
        description="Новое имя пользователя",
        examples=["Иван Иванов"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newemail@example.com",
                "full_name": "Иван Иванов"
            }
        }
    )