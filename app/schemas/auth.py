# app/schemas/auth.py
"""
Pydantic-схемы для аутентификации и авторизации.
Только валидация и сериализация — без бизнес-логики.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    """
    Запрос на регистрацию нового пользователя.
    Используется в эндпоинте POST /auth/register
    """
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="Email адрес пользователя",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Пароль (от 8 до 72 символов)",
        examples=["secure_password_123"]
    )
    full_name: str | None = Field(
        None,
        max_length=100,
        description="Имя пользователя (опционально)",
        examples=["Иван Иванов"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "student_ksenofontov@example.com",
                "password": "secure_password_123",
                "full_name": "Константин Ксенофонтов"
            }
        }
    )


class TokenResponse(BaseModel):
    """
    Ответ с токеном доступа после успешной аутентификации.
    Используется в эндпоинте POST /auth/login
    Формат совместим с OAuth2 для корректной работы Swagger UI.
    """
    access_token: str = Field(
        ...,
        description="JWT токен доступа",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        "bearer",
        description="Тип токена (всегда bearer для OAuth2)",
        examples=["bearer"]
    )
    expires_in: int | None = Field(
        None,
        description="Время жизни токена в секундах (опционально)",
        examples=[3600]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }
    )


class UserPublic(BaseModel):
    """
    Публичные данные пользователя (без чувствительной информации).
    Используется в ответах API для возврата данных пользователя.
    """
    id: int = Field(..., description="Уникальный идентификатор пользователя")
    email: EmailStr = Field(..., description="Email адрес пользователя")
    full_name: str | None = Field(None, description="Имя пользователя")
    is_active: bool = Field(True, description="Статус аккаунта")
    created_at: str | None = Field(None, description="Дата создания аккаунта (ISO 8601)")

    model_config = ConfigDict(
        from_attributes=True,  # Позволяет создавать модель из ORM-объектов
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "student_ksenofontov@example.com",
                "full_name": "Константин Ксенофонтов",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    )