# Конфигурация

## Источник настроек

Конфигурации строятся через `pydantic-settings` и читаются из YAML-файла,
путь к которому задается переменной окружения `CONFIG_FILE`.

Ключевой класс: `AppBaseSettings` в `src/infrastructure/config/__init__.py`.

## Группы настроек

- `APIWorkerSettings`:
  - `fastapi` (`FastAPISettings`)
  - `uvicorn` (`UvicornSettings`)
  - `db` (`PostgresSettings`)
- `MessageBrokerConsumerSettings`:
  - `nats`
  - `consumers`
  - `db`
- `MessageBrokerPublisherSettings`:
  - `nats`
  - `publishers`
  - `db`

## PostgreSQL

`PostgresSettings` (`src/infrastructure/config/db.py`):

- `host`, `port`, `user`, `database`
- `password_file` — путь до файла с паролем
- `pool` — параметры пула подключений

Файл `password_file` должен существовать, иначе валидатор выбросит ошибку.

## NATS

`NatsSettings` и связанные stream-конфиги находятся в `src/infrastructure/config/nats.py`.

Важно:

- часть значений по умолчанию сейчас выглядит шаблонной (не строго `transactions-users`);
- рекомендуется явно задавать значения через `CONFIG_FILE` для каждого окружения.

## Пример переменных окружения

```bash
export CONFIG_FILE=/etc/transactions-users/config.yaml
```
