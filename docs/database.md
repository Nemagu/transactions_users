# База данных и миграции

## СУБД

Целевая СУБД: PostgreSQL (в требованиях проекта указана версия 18 для production).

## Миграции

Используется `yoyo-migrations`.

Папка миграций:

- `src/infrastructure/db/postgres/migrations`

Применение миграций выполняется через функцию `apply_migrations`:

- `src/infrastructure/db/postgres/apply_migrations.py`

## Основные таблицы

По текущим миграциям создаются таблицы:

- `transactions_users_tables`
- `users`
- `users_versions`
- `users_outbox`
- `users_passwords`

## Репозитории

Postgres-адаптеры пользователей:

- `PostgresUserReadRepository`
- `PostgresUserVersionRepository`
- `PostgresUserOutboxRepository`
- `PostgresUserPasswordRepository`

Репозитории подключаются в `PostgresUnitOfWork`.

## Принципы работы репозиториев

- SQL параметризован (без f-строк);
- конфликты сохранения не подавляются SQL-конструкциями `ON CONFLICT ... DO NOTHING/UPDATE`, если это нарушает бизнес-контракт;
- для read-репозитория сохранение выполняется по версии агрегата:
  - версия `1` -> `INSERT`
  - версия `> 1` -> `UPDATE`.
