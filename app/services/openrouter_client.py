# app/services/openrouter_client.py
"""
Клиент для взаимодействия с OpenRouter API.
Только HTTP-запросы — без бизнес-логики.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
import httpx
from app.core.errors import ExternalServiceError  # ← Импорт из core.errors

# -----------------------------------------------------------------------------
# Модели данных для ответов LLM
# -----------------------------------------------------------------------------


class LLMResponse(BaseModel):
    """
    Структурированный ответ от LLM-сервиса.
    Используется для передачи данных из сервиса в usecase.
    """

    answer: str = Field(..., description="Текст ответа от модели")
    model: str = Field(..., description="Идентификатор использованной модели")
    tokens_used: Optional[int] = Field(
        None, description="Количество использованных токенов"
    )
    finish_reason: Optional[str] = Field(
        None, description="Причина завершения генерации"
    )
    conversation_id: Optional[str] = Field(
        None, description="ID диалога для продолжения"
    )


# -----------------------------------------------------------------------------
# OpenRouter Service (имя класса должно совпадать с импортом в deps.py)
# -----------------------------------------------------------------------------


class OpenRouterService:
    """
    Сервис для вызова OpenRouter API.
    Отвечает только за HTTP-взаимодействие с внешним сервисом.
    Не содержит бизнес-логики, не работает с БД напрямую.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",  # ✅ Без пробелов!
        default_model: str = "stepfun/step-3.5-flash:free",
        site_url: str = "https://example.com",
        app_name: str = "llm-fastapi-openrouter",
    ):
        """
        Инициализация сервиса.
        Args:
            api_key: API-ключ для авторизации запросов.
            base_url: Базовый URL API OpenRouter.
            default_model: Модель по умолчанию.
            site_url: URL сайта для статистики (HTTP-Referer).
            app_name: Имя приложения для статистики (X-Title).
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")  # ✅ Гарантируем отсутствие слэша в конце
        self._default_model = default_model
        self._site_url = site_url
        self._app_name = app_name
        self._timeout = 60.0

    async def generate(
        self,
        messages: List[dict[str, str]],
        temperature: float = 0.7,
        # 🔹 НЕТ параметра model — модель берётся только из self._default_model
    ) -> LLMResponse:
        """
        Сгенерировать ответ через OpenRouter API.
        Модель берётся из self._default_model (настройки .env).
        """
        # ✅ Модель ТОЛЬКО из настроек
        target_model = self._default_model

        payload = {
            "model": target_model,  # ← Используем модель из настроек
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._site_url,
            "X-Title": self._app_name,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    url=f"{self._base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"OpenRouter error {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()
                data = response.json()

                choice = data["choices"][0]
                message = choice["message"]
                usage = data.get("usage", {})

                return LLMResponse(
                    answer=message["content"],
                    model=data.get("model", target_model),
                    tokens_used=usage.get("total_tokens"),
                    finish_reason=choice.get("finish_reason"),
                )

            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    message=f"OpenRouter вернул ошибку: {e.response.status_code}",
                    service_name="OpenRouter",
                    details={"status_code": e.response.status_code},
                )
            except httpx.RequestError as e:
                raise ExternalServiceError(
                    message=f"Не удалось подключиться к OpenRouter: {str(e)}",
                    service_name="OpenRouter",
                )
            except (KeyError, IndexError, ValueError) as e:
                raise ExternalServiceError(
                    message=f"Некорректный ответ от OpenRouter: {str(e)}",
                    service_name="OpenRouter",
                )

    async def get_models(self) -> List[dict]:
        """
        Получить список доступных моделей от OpenRouter.

        Returns:
            Список словарей с информацией о моделях.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    url=f"{self._base_url}/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except Exception as e:
                raise ExternalServiceError(
                    message=f"Не удалось получить список моделей: {str(e)}",
                    service_name="OpenRouter",
                )
