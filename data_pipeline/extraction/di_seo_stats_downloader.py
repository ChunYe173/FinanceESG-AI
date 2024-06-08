""""
Script to download the SEO stats used to compute the ws_rank for an organisation.
"""
import logging
import argparse
import os
import sqlite3
from datetime import datetime
import validators
import json

from digital_identity import di_stats

logger = logging.getLogger("di_seo_stats_downloader")


def get_organisation_websites(conn: sqlite3.Connection) -> list[(int, str, str)]:
    sql = """SELECT organisations.id, organisations.name, organisations_di.url 
            FROM organisations JOIN organisations_di ON organisations.id = organisations_di.org_id
            WHERE organisations_di.di_type = 'website'"""
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    return rows


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--out_folder", type=str,
                        default="./seo_stats",
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
    out_file = os.path.join(args.out_folder, f"seo_stats_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")

    # Get list of companies with websites
    seo_stats = []
    for (org_id, org_name, org_website) in get_organisation_websites(insights_db_conn):
        logger.info(f"Processing website for {org_id} - {org_name}, {org_website}")
        if not org_website.startswith("http"):
            org_website = "http://" + org_website
        if not validators.url(org_website):
            logger.warning(f"Invalid URL {org_website}")
            continue
        try:
            stats = di_stats.extract_seo_stats(org_website)
            stats['org_id'] = org_id
            seo_stats.append(stats)
        except Exception as e:
            logger.error(f"Failed to retrieve seo stats for {org_id}-{org_name} from {org_website}")

    with open(out_file, "w") as f:
        json.dump(seo_stats, f)
    logger.info("Extraction Complete")
