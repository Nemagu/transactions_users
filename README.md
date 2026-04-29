# transactions-users

Сервис управления пользователями в экосистеме `transactions`.

Проект в разработке: на текущем этапе реализованы доменный и application-слои, а также Postgres-адаптеры и конфигурационные модели.

## Конфигурация

Настройки читаются через `pydantic-settings` из YAML-файла.
Путь до YAML передается через переменную окружения `CONFIG_FILE`.

Примеры конфигов лежат только в папке:

- `config/api_worker.yaml`
- `config/message_broker_consumer.yaml`
- `config/message_broker_publisher.yaml`

Минимально требуется подготовить файл пароля PostgreSQL, путь по умолчанию:

```text
/tmp/transactions/db_password
```

## Запуск

1. Установить зависимости:

```bash
uv sync
```

2. Указать конфиг:

```bash
export CONFIG_FILE=./config/api_worker.yaml
```

3. Применить миграции:

```python
from infrastructure.config import PostgresSettings
from infrastructure.db.postgres import apply_migrations

apply_migrations(PostgresSettings())
```

4. Проверки качества:

```bash
uv run ruff check
uv run pytest
```

5. Текущая точка входа:

```bash
uv run python src/main.py
```

`main.py` сейчас содержит заглушку и не поднимает production-процессы FastAPI/NATS.
