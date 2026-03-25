from typing import Any, Optional


class AppError(Exception):
    """
    Базовое исключение для доменных ошибок приложения .
    Используется в usecase и сервисах для сигнализации об ошибках бизнес-логики.
    Не зависит от фреймворка (FastAPI), чтобы сохранить чистоту бизнес-слоя.
    """

    # Код статуса HTTP, который должен вернуть API слой при перехвате этой ошибки.
    # По умолчанию 500 (Internal Server Error), переопределяется в наследниках.
    status_code: int = 500

    # Уникальный код ошибки для фронтенда (например, для i18n).
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class ConflictError(AppError):
    """
    Ошибка конфликта ресурсов.
    Пример: попытка регистрации с email, который уже существует.
    HTTP Mapping: 409 Conflict
    """

    status_code = 409
    error_code = "CONFLICT"


class UnauthorizedError(AppError):
    """
    Ошибка аутентификации.
    Пример: неверный пароль, истекший токен, пользователь не найден при логине.
    HTTP Mapping: 401 Unauthorized
    """

    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    """
    Ошибка авторизации (доступ запрещен).
    Пример: пользователь пытается изменить чужой ресурс или у него нет роли.
    HTTP Mapping: 403 Forbidden
    """

    status_code = 403
    error_code = "FORBIDDEN"


class NotFoundError(AppError):
    """
    Ошибка отсутствия ресурса.
    Пример: запрашиваемый объект не найден в базе данных.
    HTTP Mapping: 404 Not Found
    """

    status_code = 404
    error_code = "NOT_FOUND"


class ExternalServiceError(AppError):
    """
    Ошибка взаимодействия с внешним сервисом.
    Пример: OpenRouter вернул ошибку, платежный шлюз недоступен.
    HTTP Mapping: 502 Bad Gateway или 503 Service Unavailable
    """

    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.service_name = service_name
        if service_name:
            self.details["service_name"] = service_name