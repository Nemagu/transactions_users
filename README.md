# users

Сервис `users` отвечает за управление жизненным циклом пользователей: регистрация, подтверждение email, аутентификация, смена email, назначение ролей и публикация доменных событий.

Проект построен на гексагональной архитектуре:
- `domain` — DDD-модель и бизнес-инварианты.
- `application` — use-case слой (CQRS-команды) и порты.
- `infrastructure` — реализации портов (PostgreSQL, Redis, NATS, JWT, password manager, config).
- `presentation` — HTTP API (FastAPI) и background worker.

## Основные сценарии

- Подтверждение email перед регистрацией.
- Создание пользователя по коду подтверждения.
- Аутентификация по паролю.
- Аутентификация по одноразовому коду.
- Подтверждение и смена email.
- Назначение ролей (`admin` / `user`) и заморозка пользователя.
- Публикация событий пользователей в NATS JetStream.

## Технологии

- Python 3.14
- FastAPI + Pydantic
- PostgreSQL 18 + `psycopg`
- Redis
- NATS JetStream (`nats-py`)
- JWT (`pyjwt`, RS256)
- Миграции: `yoyo`
- Тестирование: `pytest`, `pytest-asyncio`, `pytest-cov`
- Линтинг: `ruff`

## Структура проекта

```text
src/
  application/
  domain/
  infrastructure/
  presentation/
  tests/
config/
  api_worker.yaml
  message_broker_publisher.yaml
  message_broker_consumer.yaml
env.example
main.py
```

## Конфигурация

Приложение читает настройки из YAML через `pydantic-settings`.
Путь до конфига задается переменной окружения `CONFIG_FILE`.

Примеры конфигов:
- `config/api_worker.yaml` — API-воркер
- `config/message_broker_publisher.yaml` — NATS publisher-воркер
- `config/message_broker_consumer.yaml` — задел под consumer-воркер

Переменные окружения (см. `env.example`):
- `MODE` — режим запуска: `api` или `nats_publisher`
- `CONFIG_FILE` — путь к YAML
- `APPLY_MIGRATIONS` — применять ли миграции на старте (`true/false`)

## JWT

JWT-настройки задаются в YAML (`jwt` секция):
- `algorithm` (сейчас `RS256`)
- `private_key_file`
- `public_key_file`
- `issuer`
- `audience`
- `access_token_ttl_seconds`
- `refresh_token_ttl_seconds`
- `leeway_seconds`

Ключи читаются из файлов. Для API используется извлечение `user_id` из access token через dependency.

## Локальный запуск

1. Установка зависимостей:

```bash
uv sync
```

2. Подготовка окружения:

```bash
cp env.example .env
# при необходимости: source .env
```

3. Подготовка файлов секретов (пример):

```bash
mkdir -p /tmp/users
printf 'users_password' > /tmp/users/db_password
# jwt ключи:
# /tmp/users/jwt_private_key.pem
# /tmp/users/jwt_public_key.pem
```

4. Запуск API:

```bash
export MODE=api
export CONFIG_FILE=./config/api_worker.yaml
uv run python main.py
```

5. Запуск publisher-воркера:

```bash
export MODE=nats_publisher
export CONFIG_FILE=./config/message_broker_publisher.yaml
uv run python main.py
```

## Миграции

Миграции применяются инструментом `yoyo` (используется `infrastructure.db.postgres.apply_migrations`).
При обычном старте управляются через `APPLY_MIGRATIONS=true/false`.

## Тестирование и качество

Проверка линтера:

```bash
uv run ruff check
```

Полный прогон тестов:

```bash
uv run pytest
```

Покрытие:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

Интеграционные тесты поднимают инфраструктуру автоматически через Docker Compose,
временные файлы создаются в `/tmp/users/` со случайными именами для каждой сессии.

## Docker

В образ копируется только runtime-код и необходимые файлы запуска.
Документация, примеры конфигов и тесты исключены через `.dockerignore`.

Сборка:

```bash
docker build -t users-service:local .
```

Запуск контейнера требует передать рабочий `CONFIG_FILE` и секреты/ключи, доступные внутри контейнера.

## Ограничения текущей версии

- Реализован только режим `api` и `nats_publisher`.
- Consumer-воркер пока не подключен в `main.py`.
- Часть документации по операционным сценариям (деплой, мониторинг) еще требует расширения.
