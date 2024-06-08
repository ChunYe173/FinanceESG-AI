CREATE TABLE IF NOT EXISTS organisations (
	id integer PRIMARY KEY,
	name text NOT NULL,
    sector text,
    country text,
    profile text
);