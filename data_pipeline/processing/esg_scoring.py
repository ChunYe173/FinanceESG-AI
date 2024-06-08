"""
Wrapper script to run the ESG Scoring script to process sustainability reports and produce ESG Scores for companies.
The ESG Scorer takes a path to the Sustainability Reports, processes them and generates the scores.
This script calls the ESG Scorer and based on the returned scores, updates the insights.db with the ESG Scores

ToDo: The ESG Scorer code is provided as is from the work stream and has not been optimised or refactored
    into a clean architecture - this needs to be done at a later date
"""
import datetime
import os
import sqlite3
import logging
import argparse

import pandas as pd

from esgscoring.scoring import scorer

logger = logging.getLogger("esg_scoring")


def pad_name(company_name: str) -> str:
    new_name = "".join([f" {c}" if c.isupper() else c for c in company_name]).strip()
    new_name = new_name.replace("  ", " ")
    return new_name


def find_org_by_alias(conn: sqlite3.Connection, name_to_match: str):
    sql = ("SELECT organisations.id, organisations.name FROM organisations "
           "JOIN organisations_alias ON organisations_alias.org_id = organisations.id "
           "WHERE LOWER(organisations_alias.alias) LIKE '%' || ? || '%' OR "
           "LOWER(organisations_alias.alias) LIKE '%' || ? || '%'")
    cur = conn.cursor()
    cur.execute(sql, (name_to_match.lower(), pad_name(name_to_match).lower()))
    rows = cur.fetchall()
    cur.close()
    if len(rows) == 0:
        return None, None
    else:
        return rows[0][0], rows[0][1]


def migrate_from_esg_db(db_path: str):
    companies = []
    E1 = []
    E2 = []
    E3 = []
    S1 = []
    S2 = []
    S3 = []
    G1 = []
    G2 = []
    E = []
    S = []
    G = []
    ESG = []
    conn = sqlite3.connect(db_path)
    sql = """SELECT Company, E1_ClimateChange, E2_NaturalCapital, E3_PollutionWaste, S1_HumanCapital,
        S2_ProductLiability, S3_CommunityRelations, G1_CorporateGovernance, G2_BusinessValueEthics, 
        E, S, G, ESG
        FROM ESGdash
        """

    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    if len(rows) > 0:
        for idx in range(len(rows)):
            companies.append(rows[idx][0])
            E1.append(rows[idx][1])
            E2.append(rows[idx][2])
            E3.append(rows[idx][3])
            S1.append(rows[idx][4])
            S2.append(rows[idx][5])
            S3.append(rows[idx][6])
            G1.append(rows[idx][7])
            G2.append(rows[idx][8])
            E.append(rows[idx][9])
            S.append(rows[idx][10])
            G.append(rows[idx][11])
            ESG.append(rows[idx][12])

    return companies, E1, E2, E3, S1, S2, S3, G1, G2, E, S, G, ESG


def update_esg_scores_for_org(conn, org_id, E1, E2, E3, S1, S2, S3, G1, G2, E, S, G, ESG):
    sql = """INSERT INTO organisations_esg_scores(org_id, timestamp, 
                E1_ClimateChange, E2_NaturalCapital, E3_PollutionWaste, 
                S1_HumanCapital, S2_ProductLiability, S3_CommunityRelations, 
                G1_CorporateGovernance, G2_BusinessValueEthics,
                E, S, G, ESG)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
    timestamp = datetime.datetime.now()

    cur = conn.cursor()
    cur.execute(sql, (org_id, timestamp, E1, E2, E3, S1, S2, S3, G1, G2, E, S, G, ESG))
    cur.commit()
    cur.close()


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--data_folder", type=str,
                        default="./reports",
                        help="Path to folder where the Sustainability Report files to be processed are stored")
    parser.add_argument("--insight_db", type=str,
                        default="./insights.db",
                        help="The path to the insights database file")
    parser.add_argument("--weight_e", type=float, default=0.45,
                        help="The weighting to apply to Environment scores in the overall ESG score. Default 0.45")
    parser.add_argument("--weight_s", type=float, default=0.45,
                        help="The weighting to apply to Social scores in the overall ESG score. Default 0.30")
    parser.add_argument("--weight_g", type=float, default=0.25,
                        help="The weighting to apply to Governance scores in the overall ESG score. Default 0.25")
    
    args = parser.parse_args()

    if args.data_folder is None or not os.path.exists(args.data_folder):
        raise RuntimeError(f"The path to the data could not be found or is not accessible. Path was {args.data_folder}")

    if args.insight_db is None or not os.path.exists(args.insight_db):
        raise RuntimeError(
            f"The Insights database was not found or is not accessible. Path provided was '{args.insight_db}'")

    insights_db_conn = sqlite3.connect(args.insight_db)

    # Call the ESG Scoring function to score the documents based on the contents of the folder
    companies, E1, E2, E3, S1, S2, S3, G1, G2, E, S, G, ESG = scorer(args.weight_e, args.weight_s, args.weight_g,
                                                                     args.data_folder)

    # Store these resulting scores in the Insights database
    for idx in range(len(companies)):
        # Need to attempt to find the relevant company name and id
        org_id, org_name = find_org_by_alias(insights_db_conn, companies[idx])
        if org_id is None:
            logger.warning(f"Unable to match the company name '{companies[idx]}' "
                           " to an organisation within the Insights Database")
            # Skip update
            continue
        logger.info(f"Matched scored Company '{companies[idx]}' to Organisation {org_id} - {org_name}")

        # Store the results
        update_esg_scores_for_org(insights_db_conn, org_id, E1[idx], E2[idx], E3[idx],
                                  S1[idx], S2[idx], S3[idx],
                                  G1[idx], G2[idx],
                                  E[idx], S[idx], G[idx], ESG[idx])
