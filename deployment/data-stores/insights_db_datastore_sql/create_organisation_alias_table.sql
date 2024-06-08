CREATE TABLE IF NOT EXISTS organisations_alias (
	id integer PRIMARY KEY,
    org_id integer NOT NULL,
	alias text NOT NULL,
    FOREIGN KEY (org_id) REFERENCES organisations(id)
);