"""
This python script contains a set of functions that are used to create
and initialise the data-store used for Digital Identity
"""
import sqlite3
import os
from datetime import datetime
from sqlite3 import Error, Connection
import argparse
import logging
import csv

import pandas as pd

logger = logging.getLogger("create_di_scores__datastore")
DATA_STORE_NAME = "insights.db"


def get_digital_score(linkedin_followers: int, ws_rank: float,
                      mean_linkedin_followers: float, mean_ws_rank: float,
                      frequency_ratio: float = 0.1345):
    """Calculate digital score based on specified frequency ratio."""
    return (
            linkedin_followers * frequency_ratio / mean_linkedin_followers
            + ws_rank / mean_ws_rank
    )


def _create_di(conn, org_id, di_type, di_url):
    urls = _get_di_urls(conn, org_id, di_type)
    if di_url not in urls:
        sql = """ INSERT INTO organisations_di(org_id, di_type, url)
                            VALUES(?, ?, ?)"""
        cur = conn.cursor()
        cur.execute(sql, [org_id, di_type, di_url])
        conn.commit()
        return cur.lastrowid
    return None


def _get_di_urls(conn, org_id, di_type) -> list[str]:
    sql = """SELECT url from organisations_di WHERE org_id = ? and di_type = ?"""

    cur = conn.cursor()
    cur.execute(sql, [org_id, di_type.lower()])
    rows = cur.fetchall()
    cur.close()
    return [url[0] for url in rows]


def _create_di_scores(conn: sqlite3.Connection, org_id: int, timestamp: datetime, score_type: str, score: float):
    sql = """INSERT INTO organisations_di_scores(org_id, timestamp, score_type, score)
                VALUES (?, ?, ?, ?)"""

    cur = conn.cursor()
    cur.execute(sql, [org_id, timestamp.strftime("%Y%m%d%H%M%S"), score_type, score])
    conn.commit()
    return cur.lastrowid


def find_org_by_alias(conn: sqlite3.Connection, name_to_match: str):
    sql = ("SELECT organisations.id, organisations.name FROM organisations "
           "JOIN organisations_alias ON organisations_alias.org_id = organisations.id "
           "WHERE LOWER(organisations_alias.alias) LIKE '%' || ? || '%'")
    cur = conn.cursor()
    cur.execute(sql, (name_to_match.lower(),))
    rows = cur.fetchall()
    cur.close()
    if len(rows) == 0:
        return None, None
    else:
        return rows[0][0], rows[0][1]


def initialise_datastore(path: str, delete_existing: bool = False):
    """
    Initialises the Digital Identity Scores Datastore and sets up the Schema for storing the documents.
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
    logger.info("Creating organisation_di_scoring table")
    _create_table(conn, './insights_db_datastore_sql/create_organisations_di_scores_table.sql')


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
    tables_to_drop = ["organisations_di_scores"]

    for table in tables_to_drop:
        logger.info(f"Dropping {table} table")
        cur.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()


def convert_to_int(value: str) -> int:
    value = value.replace(',', '')
    return int(value) if not pd.isna(value) else 0


def migrate_di_scores_from_csv(datastore_path: str, data_source_file: str):
    """
    Populates the datastore with some data migrated from the DI Scoring team's scoring CSV file
    This is likely only to be used once during deployment
    Params
    @datastore_path: path to the insights database where the scores are to be loaded into
    @source_data_path: path to the source DI Scoring CSV files that you want to migrate from
    """
    logger.info(f"Migrating DI Scores from {data_source_file}")
    conn = sqlite3.connect(os.path.join(datastore_path, DATA_STORE_NAME))

    if not os.path.exists(data_source_file):
        raise RuntimeError(f"The source csv file was not found at {data_source_file}")

    di_df = pd.read_csv(data_source_file)

    # Add Org ID to dataframe
    company_names = di_df['name'].tolist()
    org_ids = [find_org_by_alias(conn, name)[0] for name in company_names]
    di_df['org_id'] = [org_id if org_id is not None else -1 for org_id in org_ids]
    di_df['org_id'] = di_df['org_id'].astype(int)
    di_df.rename(columns={'Linkedin followers ': 'Linkedin followers'}, inplace=True)

    mean_linkedin_followers = di_df['Linkedin followers'].mean()
    mean_ws_score = di_df['ws_rank'].mean()

    timestamp = datetime.now()
    for idx in range(len(di_df)):
        if di_df.iloc[idx]['org_id'] >= 0:
            record = di_df.iloc[idx]
            org_id = int(record['org_id'])
            # Add LinkedIn to DI table if present
            if not pd.isna(record["Linkedin website"]):
                _create_di(conn, org_id, "linkedin", record['Linkedin website'])

            # Insert DI Scores Record
            ws_rank = float(record['ws_rank'])
            digital_score = None
            linkedin_followers = record['Linkedin followers']
            if not pd.isnull(linkedin_followers):
                digital_score = get_digital_score(linkedin_followers, ws_rank, mean_linkedin_followers, mean_ws_score)

            if ws_rank is not None and not pd.isnull(ws_rank):
                _create_di_scores(conn, org_id, timestamp, "ws_rank", ws_rank)
            if digital_score is not None:
                _create_di_scores(conn, org_id, timestamp, "digital_score", digital_score)

    logger.info("Migration complete")


if __name__ == '__main__':
    # Configure logging to STD OUT
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Path to folder where you want the Digital Identity Datastore to be created")
    parser.add_argument("--delete_existing",
                        help="Set to True if you want to delete any existing Digital Identity Datastore in the folder. "
                             "Default is False")
    parser.add_argument("--migrate_data",
                        help="Set to the path to where the DI scoring CSV files are stored if you want to migrate data to the new datastore")
    args = parser.parse_args()

    datastore_path = "." if args.path is None else args.path
    delete_existing = False if args.delete_existing is None else bool(args.delete_existing)

    initialise_datastore(datastore_path, delete_existing)

    if args.migrate_data is not None:
        migrate_di_scores_from_csv(datastore_path, args.migrate_data)
