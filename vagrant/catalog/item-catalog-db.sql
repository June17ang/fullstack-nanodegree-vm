DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS item_categories;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    status CHAR(1) NOT NULL DEFAULT 'A'
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
)

CREATE TABLE item_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status CHAR(1) NOT NULL DEFAULT 'A'
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
)

CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL DEFAULT 1,
    item_category_id INTEGER NOT NULL DEFAULT 1
    title TEXT NOT NUL,
    body TEXT NOT NULL,
    status CHAR(1) NOT NULL DEFAULT 'A'
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users (id)
    FOREIGN KEY (item_category_id) REFERENCES item_categories (id)
)