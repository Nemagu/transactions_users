-- create_users_tables
-- depends: 

BEGIN;

DROP TABLE IF EXISTS users_tables;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS users_versions;
DROP TABLE IF EXISTS users_outbox;

COMMIT;
