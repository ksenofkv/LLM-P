"""
app/core/security.py

Модуль утилит безопасности.
Отвечает за криптографические операции (хеширование, JWT).
Не содержит логики работы с БД или HTTP-слоем.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from passlib.context import CryptContext
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError

# Предполагается, что в проекте есть модуль конфигурации
# Если его нет, создайте app/core/config.py с классом Settings
try:
    from app.core.config import settings
except ImportError:
    # Fallback для примера, если конфиг еще не создан
    class MockSettings:
        SECRET_KEY: str = "your-secret-key-change-in-production"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    settings = MockSettings()

# -----------------------------------------------------------------------------
# Password Hashing (Passlib)
# -----------------------------------------------------------------------------

# Контекст для хеширования паролей. Используем bcrypt как стандарт де-факто.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли открытый пароль хешированному.
    
    :param plain_password: Пароль в открытом виде (от пользователя).
    :param hashed_password: Хеш пароля из базы данных.
    :return: True если пароль верный, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Генерирует хеш для переданного пароля.
    
    :param password: Пароль в открытом виде.
    :return: Строка хеша (bcrypt).
    """
    return pwd_context.hash(password)


# -----------------------------------------------------------------------------
# JWT Token Handling
# -----------------------------------------------------------------------------

def create_access_token(
    subject: Union[str, int], 
    role: str, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создает JWT Access Token.
    
    Формирует payload со стандартными полями:
    - sub: идентификатор пользователя (subject)
    - role: роль пользователя
    - exp: время истечения токена
    - iat: время выдачи токена
    
    :param subject: ID пользователя (будет преобразован в строку).
    :param role: Роль пользователя (например, 'user', 'admin').
    :param expires_delta: Дельта времени жизни токена. Если None, берется из конфига.
    :return: Encoded JWT token string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Текущее время в UTC
    now = datetime.now(timezone.utc)
    expire_time = now + expires_delta
    
    # Формирование payload
    to_encode = {
        "sub": str(subject),  # Subject ID обязательно строка в JWT
        "role": role,
        "iat": now,           # Issued At
        "exp": expire_time    # Expiration Time
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Декодирует и валидирует JWT Access Token.
    
    Проверяет:
    - Подпись токена (совпадает ли с SECRET_KEY).
    - Срок действия (не истек ли exp).
    - Корректность алгоритма.
    
    :param token: Строка JWT токена (из заголовка Authorization).
    :return: Payload (dict) если токен валиден, иначе None.
             Не выбрасывает исключения наружу, чтобы упростить обработку в зависимостях.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "iat", "sub"]} # Требует наличия обязательных полей
        )
        return payload
    except (ExpiredSignatureError, InvalidTokenError, PyJWTError):
        # Токен истек, подпись неверна или формат некорректен
        return None
    except Exception:
        # Любая другая непредвиденная ошибка при декодировании
        return None