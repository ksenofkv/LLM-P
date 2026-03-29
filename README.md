# protected_api_for_llm_Ksenofontov_M25-555

**Protected LLM API** — это производительный асинхронный бэкенд на FastAPI, построенный по принципам **Clean Architecture** для работы с OpenRouter.

**Цель работы**

Целью данной работы является разработка серверного приложения на FastAPI, предоставляющего защищённый API для взаимодействия с большой языковой моделью (LLM) через сервис OpenRouter. В рамках задания необходимо реализовать аутентификацию и авторизацию пользователей с использованием JWT, хранение данных в базе SQLite, а также корректно разделить ответственность между слоями приложения (API, бизнес-логика, доступ к данным).
Задание направлено на формирование практических навыков:

* работы с FastAPI и асинхронным backend,
* проектирования серверной архитектуры с разделением слоёв,
* использования JWT для аутентификации,
* интеграции внешних API (LLM),
* работы с базой данных через SQLAlchemy,
* управления зависимостями проекта через uv.

---
## Запуск

Перед запуском убедитесь, что в корневой директории проекта (рядом с файлом pyproject.toml) создан файл конфигурации 
*.env* с необходимыми параметрами конфигурации.

## Установка

Для запуска проекта вам понадобится **Python 3.12+** и установленный менеджер пакетов [**uv**].

Перед установкой, убедитесь, что у вас установлен Python, склонируйте репозиторий с помощью команды:
git clone https://github.com/ksenofkv/LLM-P.git

Переход в папку проетка
cd llm-p

Установка uv
pip install uv

Инициализация проекта
uv init 

Создание виртуального окружения
uv venv

Активировация виртуального окружения
MacOS/Linux: source .venv/bin/activate
Windows: .venv\Scripts\activate.batWindows

Установка зависимостей проекта
uv pip install -r <(uv pip compile pyproject.toml)

Зарегистрируйтесь на платформе OpenRouter и получите API-ключ. Вставьте его в файл .env в корне проекта в строку OPENROUTER_API_KEY="Ваш API-ключ"

Запуск приложения
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


При успешном запуске в терминале появятся логи, аналогичные следующим:

```shell
$ uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
INFO:     Will watch for changes in these directories: ['C:\\Users\\123\\Desktop\\python\\LLM\\llm-p']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [16728] using WatchFiles
INFO:     Started server process [28768]
INFO:     Waiting for application startup.
2026-03-29 20:42:27,408 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-29 20:42:27,408 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("users")
2026-03-29 20:42:27,408 INFO sqlalchemy.engine.Engine [raw sql] ()
2026-03-29 20:42:27,410 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("chat_messages")
2026-03-29 20:42:27,410 INFO sqlalchemy.engine.Engine [raw sql] ()
2026-03-29 20:42:27,411 INFO sqlalchemy.engine.Engine COMMIT
Database initialized: sqlite+aiosqlite:///./app.db
App started in local mode
INFO:     Application startup complete.

```

После запуска сервера перейдите в браузере по хосту `http://localhost:8000/docs`:


Проверка ruff:
```shell
123@DESKTOP-D4408P2 MINGW64 ~/Desktop/python/LLM/llm-p (main)
$ ruff check .
All checks passed!

123@DESKTOP-D4408P2 MINGW64 ~/Desktop/python/LLM/llm-p (main)
$ ruff format --check .
27 files already formatted
```

![opeapi.png](docs/img/opeapi.png)

---
## Скриншоты работы проекта для проверки

1. **Регистрация пользователя**
![Регистрация](docs/1_registration/image.png)

2. **Логин и получение JWT**
![Логин](docs/2_login/image-1.png)

3. **Авторизация через Swagger**
![Swagger Auth 1](docs/3_swagger/image-2.png)
![Swagger Auth 2](docs/3_swagger/image-3.png)

4. **Вызов POST /chat**
![Запрос в чат 1](docs/4_chat/image-4.png)
![Запрос в чат 2](docs/4_chat/image-5.png)

5. **Получение истории через GET /chat/history**
![История чата](docs/5_6_history/image-6.png)

6. **Удаление истории через DELETE /chat/history**
![Удаление истории 1](docs/5_6_history/image-7.png)
![Удаление истории 2](docs/5_6_history/image-8.png)

7. **Получение информации о текущем пользователе**
![Получение информации о пользователе 1](docs/7_profile/image-9.png)

8. **Health check**
![Состояние 1](docs/8_healt_chek/image-10.png)

---

## 🗂 Структура проекта
```
llm_p/
├── pyproject.toml                 # Зависимости проекта (uv)
├── README.md                      # Описание проекта и запуск
├── .env.example                   # Пример переменных окружения
│
├── app/
│   ├── init.py
│   ├── main.py                    # Точка входа FastAPI
│   │
│   ├── core/                      # Общие компоненты и инфраструктура
│   │   ├── init.py
│   │   ├── config.py              # Конфигурация приложения (env → Settings)
│   │   ├── security.py            # JWT, хеширование паролей
│   │   └── errors.py              # Доменные исключения
│   │
│   ├── db/                        # Слой работы с БД
│   │   ├── init.py
│   │   ├── base.py                # DeclarativeBase
│   │   ├── session.py             # Async engine и sessionmaker
│   │   └── models.py              # ORM-модели (User, ChatMessage)
│   │
│   ├── schemas/                   # Pydantic-схемы (вход/выход API)
│   │   ├── init.py
│   │   ├── auth.py                # Регистрация, логин, токены
│   │   ├── user.py                # Публичная модель пользователя
│   │   └── chat.py                # Запросы и ответы LLM
│   │
│   ├── repositories/              # Репозитории (ТОЛЬКО SQL/ORM)
│   │   ├── init.py
│   │   ├── users.py               # Доступ к таблице users
│   │   └── chat_messages.py       # Доступ к истории чатов
│   │
│   ├── services/                  # Внешние сервисы
│   │   ├── init.py
│   │   └── openrouter_client.py   # Клиент OpenRouter / LLM
│   │
│   ├── usecases/                  # Бизнес-логика приложения
│   │   ├── init.py
│   │   ├── auth.py                # Регистрация, логин, профиль
│   │   └── chat.py                # Логика общения с LLM
│   │
│   └── api/                       # HTTP-слой (тонкие эндпоинты)
│       ├── init.py
│       ├── deps.py                # Dependency Injection
│       ├── routes_auth.py         # /auth/*
│       └── routes_chat.py         # /chat/*
│
└── app.db                         # SQLite база (создаётся при запуске)
```

---

## Автор

Проект разработан студентом НИЯУ МИФИ:  
**Ксенофонтов Константин Владимирович**  
- GitHub:  https://github.com/ksenofkv

---