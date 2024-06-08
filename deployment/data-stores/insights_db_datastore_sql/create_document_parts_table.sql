CREATE TABLE IF NOT EXISTS document_parts (
	id integer PRIMARY KEY,
	document_id integer NOT NULL,
	document_part_idx integer NOT NULL,
    document_part_content text NOT NULL,
    esg_category text,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);