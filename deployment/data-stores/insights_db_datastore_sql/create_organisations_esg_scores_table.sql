CREATE TABLE organisations_esg_scores (
    id integer PRIMARY KEY,
    timestamp text NOT NULL,
    org_id integer NOT NULL,
    E1_ClimateChange float,
    E2_NaturalCapital float,
    E3_PollutionWaste float,
    S1_HumanCapital float,
    S2_ProductLiability float,
    S3_CommunityRelations float,
    G1_CorporateGovernance float,
    G2_BusinessValueEthics float,
    E float,
    S float,
    G float,
    ESG float,
    FOREIGN KEY (org_id) REFERENCES organisations(id)
);