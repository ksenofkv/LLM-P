# app/schemas/user.py
"""Публичные схемы для пользовательских данных."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class UserPublic(BaseModel):
    """Публичная схема пользователя для ответов API."""
    
    id: int = Field(..., description="ID пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    role: str = Field(..., description="Роль пользователя")
    
    # ОСТАВЛЯЕМ str — это то, что ожидает клиент в JSON
    created_at: Optional[str] = Field(None, description="Дата создания (ISO 8601)")

    # ConfigDict для Pydantic v2
    model_config = ConfigDict(from_attributes=True)

    # ВАЛИДАТОР: конвертирует datetime → str ДО проверки типа
    @field_validator("created_at", mode="before")
    @classmethod
    def _convert_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return value  # Если уже строка — возвращаем как есть


# Вспомогательный dataclass для внутренней логики (не для API)
from dataclasses import dataclass

@dataclass
class UserData:
    """Данные пользователя для внутренней работы."""
    user_id: int
    user_role: str