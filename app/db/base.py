# app/db/base.py
# =============================================================================
# ORM BASE CLASS
# Этот модуль объявляет базовый класс для всех декларативных моделей SQLAlchemy.
# Используется стиль SQLAlchemy 2.0: наследование от DeclarativeBase.
# Все модели (User, ChatMessage, etc.) наследуются от этого класса Base.
# =============================================================================

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
