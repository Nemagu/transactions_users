# transactions-users

Сервис управления пользователями в экосистеме `transactions`.

Проект строится по гексагональной архитектуре, использует DDD в `domain` и CQRS в `application`.

## Состояние проекта

Сервис находится в активной разработке.

Сейчас в репозитории реализованы базовые слои домена, application-команды и Postgres-адаптеры репозиториев пользователей.
`main.py` пока содержит заглушку и не запускает production-процесс.

## Быстрый старт

1. Установить зависимости:

```bash
uv sync
```

2. Подготовить файл пароля PostgreSQL, по умолчанию:

```text
/tmp/transactions/db_password
```

3. Применить миграции (пример):

```python
from infrastructure.config import PostgresSettings
from infrastructure.db.postgres import apply_migrations

apply_migrations(PostgresSettings())
```

4. Запустить проверки:

```bash
uv run ruff check
uv run pytest
```

## Структура

- `src/domain`: доменная модель (сущности, value objects, доменные ошибки, фабрики).
- `src/application`: use case-команды, DTO и интерфейсы портов.
- `src/infrastructure`: адаптеры (Postgres, конфигурация, заготовки брокеров и внешних интеграций).
- `src/infrastructure/db/postgres/migrations`: SQL-миграции для `yoyo`.
- `docs`: техническая документация по архитектуре и эксплуатации.

## Реализованные application-сценарии

Публичные user use case:

- создание пользователя;
- подтверждение email;
- отправка auth-кода;
- аутентификация по коду;
- аутентификация по паролю;
- смена email и подтверждение нового email;
- назначение роли admin/user;
- заморозка пользователя.

Приватные user use case:

- публикация непубликованных версий пользователя из outbox.

## Технологии

- Python 3.14+
- FastAPI
- PostgreSQL + psycopg3/pool
- NATS JetStream (`nats-py`)
- Yoyo migrations
- Pydantic + pydantic-settings
- Pytest, Ruff

## Дополнительная документация

- [Обзор архитектуры](docs/architecture.md)
- [Конфигурация и переменные](docs/configuration.md)
- [База данных и миграции](docs/database.md)
- [Разработка и качество](docs/development.md)

## Примечания

Часть значений по умолчанию в конфигурациях и именах стримов выглядит как шаблонные/унаследованные из другого сервиса (например, `companies_service`).
Перед production-использованием рекомендуется привести их к предметной области `transactions-users`.
