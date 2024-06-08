"""
Processes the downloaded website SEO stats for organisations, computes the current ws_rank and
stores this in the insights database
"""
import glob
import json
import logging
import argparse
import os
import sqlite3
from datetime import datetime

from digital_identity import compute_di_scores

logger = logging.getLogger("generate_ws_ranks")


def store_ws_rank_for_org(conn: sqlite3.Connection, org_id: int, timestamp: datetime, ws_rank: float) -> int:
    sql = "INSERT INTO organisations_di_scores (org_id, timestamp, score_type, score) VALUES (?, ?, ?, ?)"
    cur = conn.cursor()
    cur.execute(sql, [org_id, timestamp.strftime("%Y%m%d%H%M%S"), "ws_rank", ws_rank])
    conn.commit()
    return cur.lastrowid


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--data_folder", type=str,
                        default="./di_stats/",
                        help="Path to folder where the seo_stats files to be processed are stored")

    parser.add_argument("--insight_db", type=str,
                        default="./insights.db",
                        help="The path to the insights database file")

    args = parser.parse_args()

    if args.data_folder is None or not os.path.exists(args.data_folder):
        logger.error(f"The path to the data could not be found or is not accessible. Path was {args.data_folder}")
        exit()

    if args.insight_db is None or not os.path.exists(args.insight_db):
        raise RuntimeError(
            f"The Insights database was not found or is not accessible. Path provided was '{args.insight_db}'")

    insight_db_conn = sqlite3.connect(args.insight_db)
    files = glob.glob(args.data_folder + "/seo_stats_*.json")

    for file in files:
        timestamp = datetime.now()
        # Load the json file into memory as dict
        seo_stats = []
        with open(file) as f:
            seo_stats = json.load(f)

        # Process each entry in the dict to compute the ws_rank then store this in the insights database
        for stats in seo_stats:
            org_id = stats["org_id"]
            try:
                ws_rank = compute_di_scores.get_ws_rank(
                    keywords=stats['keywords'],
                    total_time=stats['total_time'],
                    errors=stats['errors'],
                    page_warnings=stats['pages'][0]['warnings'],
                    duplicate_pages=stats['duplicate_pages'])
                # Store the computed ws_rank in the insights database
                store_ws_rank_for_org(insight_db_conn, org_id, timestamp, ws_rank)

            except RuntimeError as e:
                logger.error(
                    f"Failed to compute ws_rank for organisation id {org_id} with data {stats}. Error Message: {e}")
