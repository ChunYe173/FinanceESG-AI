CREATE TABLE organisations_di_scores (
    id integer PRIMARY KEY,
    timestamp text NOT NULL,
    org_id integer NOT NULL,
    score_type text NOT NULL,
    score real NOT NULL,
    FOREIGN KEY (org_id) REFERENCES organisations(id)
);