# app/api/routes_auth.py
"""
HTTP-эндпоинты для аутентификации и авторизации.
Тонкий API слой — только вызовы usecase и обработка ошибок.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_usecase, get_current_user_id
from app.schemas.auth import RegisterRequest, UserPublic, TokenResponse
from app.usecases.auth import AuthUsecase
from app.core.errors import AppError


router = APIRouter(prefix="/auth", tags=["Auth"])


def _handle_domain_error(error: AppError) -> HTTPException:
    """
    Конвертирует доменные исключения в HTTPException для FastAPI.
    
    Это единственное место в API слое, где происходит маппинг
    доменных ошибок на HTTP-статусы.
    
    Args:
        error: Доменное исключение из usecase.
        
    Returns:
        HTTPException: Исключение с правильным статус-кодом.
    """
    return HTTPException(
        status_code=error.status_code,
        detail={
            "error": error.error_code,
            "message": error.message,
            "details": error.details,
        },
    )


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создаёт нового пользователя с указанным email и паролем.",
    responses={
        201: {"description": "Пользователь успешно создан", "model": UserPublic},
        409: {"description": "Email уже занят", "model": dict},
    },
)
async def register(
    request: RegisterRequest,
    usecase: AuthUsecase = Depends(get_auth_usecase),
) -> UserPublic:
    """
    Зарегистрировать нового пользователя.
    
    - **email**: Email адрес (должен быть уникальным)
    - **password**: Пароль (минимум 8 символов)
    - **full_name**: Имя пользователя (опционально)
    
    Возвращает публичные данные созданного пользователя.
    """
    try:
        user = await usecase.register(request)
        return user
    except AppError as e:
        raise _handle_domain_error(e)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему (OAuth2)",
    description="Аутентифицирует пользователя и возвращает JWT-токен для доступа к защищённым эндпоинтам.",
    responses={
        200: {"description": "Токен успешно получен", "model": TokenResponse},
        401: {"description": "Неверные учётные данные", "model": dict},
    },
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    usecase: AuthUsecase = Depends(get_auth_usecase),
) -> TokenResponse:
    """
    Войти в систему и получить JWT-токен.
    
    **OAuth2PasswordRequestForm:**
    - **username**: Email адрес пользователя (используется поле username)
    - **password**: Пароль пользователя
    
    **Важно для Swagger:**
    После успешного логина нажмите кнопку "Authorize" в Swagger UI
    и вставьте полученный токен для доступа к защищённым эндпоинтам.
    
    Возвращает:
    - **access_token**: JWT-токен для авторизации
    - **token_type**: Тип токена (всегда "bearer")
    """
    try:
        # OAuth2 использует поле 'username', но в домене у нас 'email'
        token = await usecase.login(email=form.username, password=form.password)
        return token
    except AppError as e:
        raise _handle_domain_error(e)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Получить профиль текущего пользователя",
    description="Возвращает данные аутентифицированного пользователя. Требуется JWT-токен.",
    responses={
        200: {"description": "Профиль успешно получен", "model": UserPublic},
        401: {"description": "Токен недействителен или отсутствует", "model": dict},
        404: {"description": "Пользователь не найден", "model": dict},
    },
)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    usecase: AuthUsecase = Depends(get_auth_usecase),
) -> UserPublic:
    """
    Получить профиль текущего пользователя.
    
    **Требуется авторизация:**
    Передайте JWT-токен в заголовке: `Authorization: Bearer <token>`
    
    В Swagger UI используйте кнопку "Authorize" для установки токена.
    
    Возвращает публичные данные пользователя:
    - **id**: Уникальный идентификатор
    - **email**: Email адрес
    - **role**: Роль пользователя
    - **is_active**: Статус аккаунта
    - **created_at**: Дата создания
    """
    try:
        user = await usecase.get_user_profile(user_id)
        return user
    except AppError as e:
        raise _handle_domain_error(e)