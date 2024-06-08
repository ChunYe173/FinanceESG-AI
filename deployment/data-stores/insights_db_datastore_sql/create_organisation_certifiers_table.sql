CREATE TABLE IF NOT EXISTS organisation_certifiers (
	id integer PRIMARY KEY,
    org_id integer NOT NULL,
	certifier text NOT NULL,
    membership_number text,
    scheme text,
    FOREIGN KEY (org_id) REFERENCES organisations(id)
);