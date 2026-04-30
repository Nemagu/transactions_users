-- create_users_tables
-- depends: 

BEGIN;

CREATE TABLE IF NOT EXISTS users_tables (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(256) NOT NULL UNIQUE,
    status VARCHAR(30) NOT NULL,
    state VARCHAR(30) NOT NULL,
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users_versions (
    user_version_id UUID PRIMARY KEY DEFAULT uuidv7(),
    user_id UUID NOT NULL REFERENCES users ON DELETE RESTRICT,
    email VARCHAR(256) NOT NULL,
    status VARCHAR(30) NOT NULL,
    state VARCHAR(30) NOT NULL,
    version INTEGER NOT NULL,
    event VARCHAR(30) NOT NULL,
    editor_id UUID REFERENCES users ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (user_id, version)
);

CREATE TABLE IF NOT EXISTS users_outbox (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    user_id UUID NOT NULL REFERENCES users ON DELETE RESTRICT,
    version INTEGER NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (user_id, version)
);

INSERT INTO users_tables (name)
VALUES ('users'),
('users_versions'),
('users_outbox');

COMMIT;
