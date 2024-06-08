"""
This python script contains a set of functions that are used to create an initialise the data-stores used
"""
import sqlite3
import os
from sqlite3 import Error, Connection
import argparse
import logging
import csv

logger = logging.getLogger("create_document_datastore")
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
    logger.info("Creating documents table")
    _create_table(conn, './insights_db_datastore_sql/create_documents_table.sql')
    logger.info("Creating document_parts table")
    _create_table(conn, './insights_db_datastore_sql/create_document_parts_table.sql')
    logger.info("Creating document_part_scores table")
    _create_table(conn, './insights_db_datastore_sql/create_document_part_scores_table.sql')
    logger.info("Creating document_controversy table")
    _create_table(conn, './insights_db_datastore_sql/create_document_controversy_table.sql')
    logger.info("Creating document_keywords table")
    _create_table(conn, './insights_db_datastore_sql/create_document_keywords_table.sql')
    logger.info("Creating document_entities table")
    _create_table(conn, './insights_db_datastore_sql/create_document_entities_table.sql')


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


def delete_existing_datastore(conn: Connection):
    # DB exists so drop existing tables
    cur = conn.cursor()
    tables_to_drop = ["document_entities", "document_controversy", "document_keywords", "document_part_scores",
                      "document_parts", "documents"]

    for table in tables_to_drop:
        logger.info(f"Dropping {table} table")
        cur.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Path to folder where you want the Document Datastore to be created")
    parser.add_argument("--delete_existing",
                        help="Set to True if you want to delete any existing Document Datastore in the folder. "
                             "Default is False")
    args = parser.parse_args()

    datastore_path = "." if args.path is None else args.path
    delete_existing = False if args.delete_existing is None else bool(args.delete_existing)

    initialise_document_datastore(datastore_path, delete_existing)
