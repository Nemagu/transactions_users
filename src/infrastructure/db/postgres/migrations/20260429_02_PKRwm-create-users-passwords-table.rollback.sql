-- create_users_passwords_table
-- depends: 20260429_01_KxYwa-create-users-tables

BEGIN;

DROP TABLE IF EXISTS users_passwords;

DELETE FROM users_tables
WHERE name = 'users_passwords';

COMMIT;
