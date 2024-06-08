CREATE TABLE IF NOT EXISTS organisation_licences (
	id integer PRIMARY KEY,
    org_id integer NOT NULL,
	certifier text NOT NULL,
    licence_state boolean NOT NULL,
    last_checked_date text NOT NULL,
    FOREIGN KEY (org_id) REFERENCES organisations(id)
);