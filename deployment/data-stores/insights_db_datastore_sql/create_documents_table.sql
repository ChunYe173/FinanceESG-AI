CREATE TABLE IF NOT EXISTS documents (
	id integer PRIMARY KEY,
	source_url text,
    source_country text,
	timestamp text NOT NULL,
	org_id integer,
	doc_type text NOT NULL,
	esg_category text,
	sentiment real,
    FOREIGN KEY (id) REFERENCES organisations(id)
);