# Архитектура

## Подход

Проект следует гексагональной архитектуре:

- бизнес-логика изолирована в `domain`;
- application-слой определяет сценарии и порты;
- инфраструктура реализует порты через конкретные адаптеры.

Это снижает связанность и позволяет менять детали хранения/доставки событий без изменения доменной модели.

## Слои

## `domain`

Содержит инварианты и поведение сущности пользователя:

- `User` (`src/domain/user/entity.py`);
- `UserID`, `Email`, `UserStatus`, `UserState` (`src/domain/user/value_objects.py`);
- доменные ошибки (`src/domain/errors.py`);
- фабрика восстановления/создания агрегата (`src/domain/user/factory.py`).

Правила:

- value objects неизменяемые;
- модификация приватных полей агрегата выполняется только методами агрегата;
- доменная модель не знает об инфраструктуре.

## `application`

Содержит CQRS-команды и порты:

- публичные use case пользователя: `src/application/command/public/user/*`;
- приватные use case: `src/application/command/private/user/*`;
- интерфейсы репозиториев и инфраструктурных зависимостей: `src/application/ports/*`.

`UnitOfWork` является основным контрактом транзакционной работы use case.

## `infrastructure`

Реализации портов и конфигурация:

- Postgres-репозитории: `src/infrastructure/db/postgres/*`;
- PostgreSQL UnitOfWork: `src/infrastructure/db/postgres/unit_of_work.py`;
- менеджер соединений: `src/infrastructure/db/postgres/connection.py`;
- настройки приложения: `src/infrastructure/config/*`.

## Текущие ограничения

- Входные точки FastAPI/NATS worker пока не собраны в production runtime.
- `main.py` — технологическая заглушка.
- Интеграционные адаптеры (`email`, `key_value`, `masage_broker`) частично представлены каркасом.
