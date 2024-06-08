"""
This python script contains a set of functions that are used to create an initialise the data-stores used
"""
import sqlite3
import os
from datetime import datetime
from sqlite3 import Error, Connection
import argparse
import logging
import csv

logger = logging.getLogger("create_esg_scores__datastore")
DATA_STORE_NAME = "insights.db"


def initialise_datastore(path: str, delete_existing: bool = False):
    """
    Initialises the Document Datastore and sets up the Schema for storing the documents.
    For this MVP, the datastore is a local SQLite database.

    Params
    ------
    path: str The path to the folder where the datastore is to be located.
    delete_existing: bool Set to True to delete the existing Document Data Store in the specified folder
                            or False otherwise. Default if False
    """
    db_path = os.path.join(path, DATA_STORE_NAME)

    # Create the folder structure if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)

    conn = sqlite3.connect(db_path)
    if delete_existing:
        delete_existing_datastore(conn)
    # Create tables
    logger.info("Creating organisation_esg_scoring table")
    _create_table(conn, './insights_db_datastore_sql/create_organisations_esg_scores_table.sql')


def _create_table(conn: Connection, script_path: str):
    """Creates a table in the database from sql create table script"""
    sql = ""
    # Create the Main Document Table
    with open(script_path) as f:
        sql = "\n".join(f.readlines())

    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Error as e:
        raise RuntimeError(f"Failed to create Table. {e}")


def _execute_sql_template(conn: Connection, template_path: str, data: list):
    sql = ""
    with open(template_path) as f:
        sql = "\n".join(f.readlines())
    try:
        cur = conn.cursor()
        cur.executemany(sql, data)
        conn.commit()
    except Error as e:
        raise RuntimeError(f"Failed to execute SQL statement. {e}")


def delete_existing_datastore(conn: Connection):
    # DB exists so drop existing tables
    cur = conn.cursor()
    tables_to_drop = ["organisations_esg_scores"]

    for table in tables_to_drop:
        logger.info(f"Dropping {table} table")
        cur.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()


def get_source_esg_scores(conn: Connection):
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


def update_esg_scores_for_org(conn, org_id, E1, E2, E3, S1, S2, S3, G1, G2, E, S, G, ESG):
    sql = """INSERT INTO organisations_esg_scores(org_id, timestamp, 
                E1_ClimateChange, E2_NaturalCapital, E3_PollutionWaste, 
                S1_HumanCapital, S2_ProductLiability, S3_CommunityRelations, 
                G1_CorporateGovernance, G2_BusinessValueEthics,
                E, S, G, ESG)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    cur = conn.cursor()
    cur.execute(sql, (org_id, timestamp, E1, E2, E3, S1, S2, S3, G1, G2, E, S, G, ESG))
    conn.commit()
    cur.close()


def migrate_esg_scores_from_db(datastore_path: str, source_data_path: str):
    """
    Populates the datastore with some data migrated from the ESG Scoring team's ESGdatabase
    This is likely only to be used once during deployment
    Params
    @datastore_path: path to the insights database where the scores are to be loaded into
    @source_data_path: path to the source ESGdatabase file that you want to migrate from

    """
    db_path = os.path.join(datastore_path, DATA_STORE_NAME)
    if not os.path.exists(db_path):
        raise RuntimeError(f"The Document Datastore could not be found at '{db_path}'")

    if not os.path.exists(source_data_path):
        raise RuntimeError(f"The Source ESGdatabase could not be found at '{source_data_path}'")

    insights_db_conn = sqlite3.connect(db_path)
    source_esg_db_conn = sqlite3.connect(source_data_path)

    # Get source scores
    companies, E1, E2, E3, S1, S2, S3, G1, G2, E, S, G, ESG = get_source_esg_scores(source_esg_db_conn)
    # Migrate the source scores into the insights dataabase
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


if __name__ == '__main__':
    # Configure logging to STD OUT
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Path to folder where you want the Document Datastore to be created")
    parser.add_argument("--delete_existing",
                        help="Set to True if you want to delete any existing Document Datastore in the folder. "
                             "Default is False")
    parser.add_argument("--migrate_data",
                        help="Set to the path to where the esg scoring database is stored if you want to migrate data to the new datastore")
    args = parser.parse_args()

    datastore_path = "." if args.path is None else args.path
    delete_existing = False if args.delete_existing is None else bool(args.delete_existing)

    initialise_datastore(datastore_path, delete_existing)

    if args.migrate_data is not None:
        migrate_esg_scores_from_db(datastore_path, args.migrate_data)
