# app/core/security.py
"""
Модуль утилит безопасности.
Отвечает за криптографические операции (хеширование, JWT).
Не содержит логики работы с БД или HTTP-слоем.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.core.config import settings

# -----------------------------------------------------------------------------
# Module-level constants (для импорта в deps.py и других модулях)
# -----------------------------------------------------------------------------

ALGORITHM: str = settings.jwt_alg
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.access_token_expire_minutes
SECRET_KEY: str = settings.jwt_secret

# -----------------------------------------------------------------------------
# Password Hashing (Passlib + bcrypt)
# -----------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли открытый пароль хешированному.
    :param plain_password: Пароль в открытом виде (от пользователя).
    :param hashed_password: Хеш пароля из базы данных.
    :return: True если пароль верный, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:  # ✅ Переименовано из get_password_hash
    """
    Генерирует хеш для переданного пароля.
    :param password: Пароль в открытом виде.
    :return: Строка хеша (bcrypt).
    """
    return pwd_context.hash(password)


# -----------------------------------------------------------------------------
# JWT Token Handling (python-jose)
# -----------------------------------------------------------------------------


def create_access_token(
    subject: Union[str, int], role: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создает JWT Access Token.
    :param subject: ID пользователя (будет преобразован в строку).
    :param role: Роль пользователя (например, 'user', 'admin').
    :param expires_delta: Дельта времени жизни токена. Если None, берется из конфига.
    :return: Encoded JWT token string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    expire_time = now + expires_delta

    to_encode = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire_time.timestamp()),
    }

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Декодирует и валидирует JWT Access Token.
    :param token: Строка JWT токена (из заголовка Authorization).
    :return: Payload (dict) если токен валиден, иначе None.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True, "require": ["exp", "sub"]},
        )
        return payload
    except JWTError:
        return None
    except Exception:
        return None
