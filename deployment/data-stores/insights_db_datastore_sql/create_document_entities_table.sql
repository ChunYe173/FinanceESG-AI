CREATE TABLE IF NOT EXISTS document_entities (
	id integer PRIMARY KEY,
	document_id integer NOT NULL,
	entity text NOT NULL,
	entity_type NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);