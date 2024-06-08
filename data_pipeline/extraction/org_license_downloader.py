"""
Script to download the license information for organisations from trusted certifying organisations
"""
import logging
import argparse
import os
import sqlite3
from datetime import datetime
from digital_identity import license_checker

from utils.webdriver_utils import DriverManager

logger = logging.getLogger("org_license_downloader")
def get_organisation_names(conn: sqlite3.Connection) -> list[(int, str)]:
    sql = """SELECT organisations.id, organisations.name FROM organisations"""
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    return rows


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--out_folder", type=str,
                        default="./licenses",
                        help="Path to folder where the downloaded stats are to be stored for downstream processing")
    parser.add_argument("--insight_db", type=str,
                        default="./insights.db",
                        help="The path to the insights database file")

    args = parser.parse_args()

    if not os.path.exists(args.out_folder):
        os.makedirs(args.out_folder)

    if args.insight_db is None or not os.path.exists(args.insight_db):
        raise RuntimeError(
            f"The Insights database was not found or is not accessible. Path provided was '{args.insight_db}'")

    insights_db_conn = sqlite3.connect(args.insight_db)
    out_file = os.path.join(args.out_folder, f"org_certifications_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")

    driver_manager = DriverManager()

    # Get list of companies with LinkedIn sites
    linkedin_stats = []
    for (org_id, org_name) in get_organisation_names(insights_db_conn):
        logger.info(f"Processing certifications for {org_id} - {org_name}")
        rspo_certified = license_checker.check_for_RSPO_license(driver_manager.get_webdriver_instance(), org_name)




    logger.info("Extraction Complete")
