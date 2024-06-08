CREATE TABLE IF NOT EXISTS document_keywords (
	id integer PRIMARY KEY,
	document_id integer NOT NULL,
	keyword text NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);