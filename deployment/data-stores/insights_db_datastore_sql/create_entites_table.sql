CREATE TABLE IF NOT EXISTS named_entities (
	id integer PRIMARY KEY,
	entity TEXT NOT NULL,
	entity_type text NOT NULL,
	description text NOT NULL,
    alias text NOT NULL
);