-- create_users_passwords_table
-- depends: 20260429_01_KxYwa-create-users-tables

BEGIN;

CREATE TABLE IF NOT EXISTS users_passwords (
    password_id UUID PRIMARY KEY DEFAULT uuidv7(),
    password_hash TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users ON DELETE CASCADE UNIQUE
);

INSERT INTO transactions_users_tables (name)
VALUES ('users_passwords');

COMMIT;
