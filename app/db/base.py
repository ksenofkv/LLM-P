# app/db/base.py
# =============================================================================
# ORM BASE CLASS
# 
# Этот модуль объявляет базовый класс для всех декларативных моделей SQLAlchemy.
# Используется современный стиль SQLAlchemy 2.0: наследование от DeclarativeBase.
# 
# Все модели (User, ChatMessage, etc.) должны наследоваться от этого класса Base.
# =============================================================================

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Базовый класс для ORM-моделей.
    
    Пример использования:
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            email = Column(String, unique=True)
    
    Преимущества DeclarativeBase (SQLAlchemy 2.0):
    - Лучшая поддержка type hints и автодополнения в IDE
    - Явное наследование вместо магической функции
    - Встроенная поддержка миграций и инспекции метаданных
    """
    pass