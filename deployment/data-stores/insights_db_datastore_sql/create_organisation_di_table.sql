CREATE TABLE IF NOT EXISTS organisations_di (
	id integer PRIMARY KEY,
    org_id integer NOT NULL,
	di_type text NOT NULL,
    url text NOT NULL,
    FOREIGN KEY (org_id) REFERENCES organisations(id)
);