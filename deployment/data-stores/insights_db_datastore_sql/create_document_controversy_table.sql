CREATE TABLE IF NOT EXISTS document_controversy (
	id integer PRIMARY KEY,
	document_id integer NOT NULL,
	controversy_content text NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);