"""
This python script contains a set of functions that are used to create an initialise the data-stores used
"""
import sqlite3
import os
from sqlite3 import Error, Connection
import argparse
import logging
import csv

import pandas as pd

logger = logging.getLogger("create_organisation_datastore")
DATA_STORE_NAME = "insights.db"


def initialise_document_datastore(path: str, delete_existing: bool = False):
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
    logger.info("Creating organisations table")
    _create_table(conn, './insights_db_datastore_sql/create_organisations_table.sql')

    logger.info("Creating organisation_alias table")
    _create_table(conn, './insights_db_datastore_sql/create_organisation_alias_table.sql')

    logger.info("Creating organisation_di table")
    _create_table(conn, './insights_db_datastore_sql/create_organisation_di_table.sql')

    logger.info("Creating organisation_certifiers table")
    _create_table(conn, './insights_db_datastore_sql/create_organisation_certifiers_table.sql')

    logger.info("Creating organisation_licences table")
    _create_table(conn, './insights_db_datastore_sql/create_organisation_licences_table.sql')


def _create_table(conn: Connection, script_path: str):
    """Creates a table in the database from sql create table script"""
    sql = ""
    # Create the Table
    with open(script_path) as f:
        sql = "\n".join(f.readlines())

    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Error as e:
        raise RuntimeError(f"Failed to create Table. {e}")


def get_organisations_data(data_path: str) -> list:
    data = []
    with open(data_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)  # Skip the header
        for row in csv_reader:
            data.append((row[0], row[1], row[2], row[3], row[4], float(row[5])))
    return data


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
    tables_to_drop = ["organisations", "organisation_certifiers", "organisation_licences", "organisations_alias"
                      "organisations_di", "organisations_esg_scores"]

    for table in tables_to_drop:
        logger.info(f"Dropping {table} table")
        cur.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()

def _create_alias(conn, org_id, alias_name):
    sql = """ INSERT INTO organisations_alias(org_id, alias)
                        VALUES(?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [org_id, alias_name])
    conn.commit()
    return cur.lastrowid

def _create_di(conn, org_id, di_type, di_url):
    sql = """ INSERT INTO organisations_di(org_id, di_type, url)
                        VALUES(?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [org_id, di_type, di_url])
    conn.commit()
    return cur.lastrowid


def _create_org(conn, org_name, country, sector, profile):
    sql = """ INSERT INTO organisations(name, sector, country, profile)
                    VALUES(?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [org_name, sector, country, profile])
    conn.commit()
    return cur.lastrowid


def _create_org_certification(conn, org_id, certifier, member_id, sector):
    sql = """ INSERT INTO organisation_certifiers(org_id, certifier, membership_number, scheme)
                    VALUES(?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [org_id, certifier, member_id, sector])
    conn.commit()
    return cur.lastrowid


def load_org_data(datastore_path: str, data_path: str):
    """
    Populates the organization datastore with data from the specified folder
    Params
    ------
    datastore_path: the path to the folder where the document datastore is located
    """
    db_path = os.path.join(datastore_path, DATA_STORE_NAME)
    if not os.path.exists(db_path):
        raise RuntimeError(f"The Organisation Datastore could not be found at '{db_path}'")

    if not os.path.exists(data_path):
        raise RuntimeError(f"The Organisation datafile could not be found at '{data_path}'")

    conn = sqlite3.connect(db_path)
    # Populate with org data
    logger.info("Loading Data into organization table")
    org_data = pd.read_csv(data_path)
    num_orgs = org_data.shape[0]
    for idx in range(num_orgs):
        org_name = org_data.iloc[idx]['name']
        country = org_data.iloc[idx]['country']
        sector = org_data.iloc[idx]['sector']
        certifier = org_data.iloc[idx]['certifier_site']
        member_id = org_data.iloc[idx]['member_id']
        website = org_data.iloc[idx]['website']
        profile = org_data.iloc[idx]['profile']
        org_id = _create_org(conn, org_name, country, sector, profile)
        _create_alias(conn, org_id, org_name)
        _create_di(conn, org_id, "website", website)
        if not pd.isnull(org_data.iloc[idx]['linkedin']):
            _create_di(conn, org_id, "linkedin", org_data.iloc[idx]['linkedin'])
        _create_org_certification(conn, org_id, certifier, member_id, sector)


if __name__ == '__main__':
    # Configure logging to STD OUT
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Path to folder where you want the Organisation Datastore to be created")
    parser.add_argument("--delete_existing",
                        help="Set to True if you want to delete any existing Organisation Datastore in the folder. "
                             "Default is False")
    parser.add_argument("--load_data",
                        help="Set to path to the folder where the Organization data is if you want to load the"
                             " datastore; otherwise omit to begin with an empty datastore")

    args = parser.parse_args()

    datastore_path = "." if args.path is None else args.path
    delete_existing = False if args.delete_existing is None else bool(args.delete_existing)

    initialise_document_datastore(datastore_path, delete_existing)

    if args.load_data is not None:
        if not os.path.exists(args.load_data):
            raise RuntimeError(f"Unable to load Organisation Data. The path is no accessible ({args.load_data}")
        load_org_data(datastore_path, args.load_data)
