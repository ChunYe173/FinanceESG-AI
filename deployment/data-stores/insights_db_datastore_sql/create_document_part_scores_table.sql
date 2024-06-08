CREATE TABLE IF NOT EXISTS document_part_scores (
	id integer PRIMARY KEY,
	document_id integer NOT NULL,
	document_part_idx integer NOT NULL,
    score_type text NOT NULL,
    score real NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);