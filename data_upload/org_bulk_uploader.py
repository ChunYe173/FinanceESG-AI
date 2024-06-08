import argparse
import logging
import os
import sqlite3
from datetime import datetime

import pandas as pd

logger = logging.getLogger('org_bulk_uploader')


# def load_org_data(datastore_path: str, data_path: str):
#     """
#     Populates the organization datastore with data from the specified folder
#     Params
#     ------
#     datastore_path: the path to the folder where the document datastore is located
#     """
#     db_path = os.path.join(datastore_path, DATA_STORE_NAME)
#     if not os.path.exists(db_path):
#         raise RuntimeError(f"The Organisation Datastore could not be found at '{db_path}'")
#
#     if not os.path.exists(data_path):
#         raise RuntimeError(f"The Organisation datafile could not be found at '{data_path}'")
#
#     conn = sqlite3.connect(db_path)
#     # Populate with org data
#     logger.info("Loading Data into organization table")
#     org_data = pd.read_csv(data_path)
#     num_orgs = org_data.shape[0]
#     for idx in range(num_orgs):
#         org_name = org_data.iloc[idx]['name']
#         country = org_data.iloc[idx]['country']
#         sector = org_data.iloc[idx]['sector']
#         certifier = org_data.iloc[idx]['certifier_site']
#         member_id = org_data.iloc[idx]['member_id']
#         website = org_data.iloc[idx]['website']
#         profile = org_data.iloc[idx]['profile']
#         org_id = _create_org(conn, org_name, country, sector, profile)
#         _create_alias(conn, org_id, org_name)
#         _create_di(conn, org_id, "website", website)
#         if not pd.isnull(org_data.iloc[idx]['linkedin']):
#             _create_di(conn, org_id, "linkedin", org_data.iloc[idx]['linkedin'])
#         _create_org_certification(conn, org_id, certifier, member_id, sector)


def is_existing_org(conn: sqlite3.Connection, org_name: str) -> bool:
    sql = """SELECT organisations.id FROM organisations WHERE LOWER(name) = ? LIMIT 1"""
    cur = conn.cursor()
    cur.execute(sql, [org_name.strip().lower(), ])
    rows = cur.fetchall()
    cur.close()
    return len(rows) > 0


def _insert_new_organisation(conn: sqlite3.Connection, org_name, sector, country, profile) -> int:
    sql = """ INSERT INTO organisations(name, sector, country, profile)
                        VALUES(?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [org_name, sector, country, profile])
    conn.commit()
    return cur.lastrowid


def _insert_new_organisation_di(conn: sqlite3.Connection, org_id: int, di_type: str, di_url: str) -> int:
    sql = """ INSERT INTO organisations_di(org_id, di_type, url)
                            VALUES(?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [org_id, di_type, di_url])
    conn.commit()
    return cur.lastrowid


def _get_existing_org_details(conn: sqlite3.Connection, org_name: str) -> dict:
    sql = """SELECT organisations.id, organisations.name, organisations.sector, 
                organisations.country, organisations.profile FROM organisations WHERE LOWER(name) = ? LIMIT 1"""
    cur = conn.cursor()
    cur.execute(sql, [org_name.strip().lower(), ])
    rows = cur.fetchall()
    cur.close()
    return {"id": int(rows[0][0]),
            "name": str(rows[0][1]),
            "sector": rows[0][2],
            "country": rows[0][3],
            "profile": rows[0][4]}


def _update_existing_organisation(conn: sqlite3.Connection, org_id: int, sector: str, country: str, profile: str):
    sql = """UPDATE organisations 
                SET sector = ?,
                country = ?,
                profile = ?
                WHERE id = ?"""
    cur = conn.cursor()
    cur.execute(sql, [sector, country, profile, org_id])
    conn.commit()
    cur.close()


def _get_organisation_di(conn: sqlite3.Connection, org_id: int, di_type: str):
    sql = """SELECT url from organisations_di
            WHERE org_id = ? AND di_type = ? LIMIT 1"""
    cur = conn.cursor()
    cur.execute(sql, [org_id, di_type.lower()])
    rows = cur.fetchall()
    cur.close()
    if len(rows) == 0:
        return None
    else:
        return rows[0][0]


def _update_existing_organisation_di(conn: sqlite3.Connection, org_id: int, di_type: str, di_url: str):
    sql = """UPDATE organisations_di
            SET url = ?
            WHERE org_id = ? and di_type = ?"""
    cur = conn.cursor()
    cur.execute(sql, [di_url, org_id, di_type])
    conn.commit()
    cur.close()


def _process_org_file(conn: sqlite3.Connection, data_path: str, insert_mode: bool) -> pd.DataFrame:
    logger.info(f"Processing file {args.data}")
    # Load the CSV into Pandas
    org_df = pd.read_csv(data_path)
    num_orgs = org_df.shape[0]
    column_names = org_df.columns.tolist()
    rejects_df = pd.DataFrame(columns=column_names)
    # Process each organisation
    for idx in range(num_orgs):
        org_name = org_df.iloc[idx]['name'].strip()
        org_sector = org_df.iloc[idx]['sector'].strip() if "sector" in column_names else None
        org_country = org_df.iloc[idx]['country'].strip() if "country" in column_names else None
        org_website = org_df.iloc[idx]['website'].strip() if "website" in column_names else None
        org_linkedin = org_df.iloc[idx]['linkedin'].strip() if "linkedin" in column_names else None
        org_profile = org_df.iloc[idx]['profile'].strip() if "profile" in column_names else None
        is_existing = is_existing_org(conn, org_name.strip().lower())

        if insert_mode:
            if is_existing:
                logger.info(f"Record {idx + 1} for organisation '{org_name}' already exists. Rejecting as duplicate.")
                rejects_df.loc[len(rejects_df)] = org_df.iloc[idx]

            else:
                org_id = _insert_new_organisation(conn, org_name, org_sector, org_country, org_profile)
                if org_linkedin is not None:
                    _insert_new_organisation_di(conn, org_id, "linkedin", org_linkedin)
                if org_website is not None:
                    _insert_new_organisation_di(conn, org_id, "website", org_website)
        elif not insert_mode:
            if not is_existing:
                logger.info(
                    f"Record {idx + 1} for organisation '{org_name}' was not found in the database. Rejecting as not found.")
                rejects_df.loc[len(rejects_df)] = org_df.iloc[idx]
            else:
                # Get existing details
                existing_org_details = _get_existing_org_details(conn, org_name)
                org_id = existing_org_details['id']
                if org_sector is None:
                    org_sector = existing_org_details['sector']
                if org_country is None:
                    org_country = existing_org_details['country']
                if org_profile is None:
                    org_profile = existing_org_details['profile']

                _update_existing_organisation(conn, org_id, org_sector, org_country, org_profile)
                if org_website is not None:
                    if _get_organisation_di(conn, org_id, "website") is None:
                        _insert_new_organisation_di(conn, org_id, "website", org_website)
                    else:
                        _update_existing_organisation_di(conn, org_id, "website", org_website)
                if org_linkedin is not None:
                    if _get_organisation_di(conn, org_id, "linkedin") is None:
                        _insert_new_organisation_di(conn, org_id, "linkedin", org_linkedin)
                    else:
                        _update_existing_organisation_di(conn, org_id, "linkedin", org_linkedin)
    return rejects_df


if __name__ == '__main__':
    # Configure logging to STD OUT
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--insight_db", type=str, required=True,
                        help="The path to the insights database you want the organisations to be loaded into")
    parser.add_argument("--data", type=str, required=True,
                        help="The path to the CSV file containing the organisation details to be loaded")
    parser.add_argument("--mode", type=str,
                        default="insert",
                        help="Set to 'insert' to insert the new organisations or "
                             "'update' to only update existing organisations in the insights database. "
                             "Default is 'insert'")

    args = parser.parse_args()

    # Check arguments
    if not os.path.exists(args.insight_db):
        raise ValueError(f"The insights_db path was not accessible. Path provided was '{args.insight_db}'")
    if not os.path.exists(args.data):
        raise ValueError(f"The path to the CSV file was not accessible. Path provided was '{args.data}'")
    if args.mode.lower() != "insert" and args.mode.lower() != "update":
        raise ValueError(f"The mode must be either 'insert' or 'update'. The value provided was '{args.mode}'")

    insights_db_conn = sqlite3.connect(args.insight_db)

    logger.info(f"Running Org Bulk Uploader in {args.mode} mode")
    rejects = _process_org_file(insights_db_conn, args.data, args.mode.lower() == 'insert')

    if rejects.shape[0] > 0:
        rejects_file_name = f"{args.mode.lower()}_rejects_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        logger.warning(f"There were {rejects.shape[0]} rejected rows. Saving to {rejects_file_name}")
        rejects.to_csv(rejects_file_name, index=False)
    logger.info("Finished processing")
