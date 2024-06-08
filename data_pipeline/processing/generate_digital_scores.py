"""
Processes the downloaded LinkedIn Stats for organisations, computes the current digital score and
stores this in the insights database
"""
import glob
import json
import logging
import argparse
import os
import sqlite3
from datetime import datetime
from statistics import mean

from digital_identity import compute_di_scores

logger = logging.getLogger("generate_digital_score")


def store_digital_score_for_org(conn: sqlite3.Connection, org_id: int, timestamp: datetime, ws_rank: float) -> int:
    sql = "INSERT INTO organisations_di_scores (org_id, timestamp, score_type, score) VALUES (?, ?, ?, ?)"
    cur = conn.cursor()
    cur.execute(sql, [org_id, timestamp.strftime("%Y%m%d%H%M%S"), "digital_score", ws_rank])
    conn.commit()
    return cur.lastrowid


def get_lastest_ws_rank_for_org(conn: sqlite3.Connection, org_id: int) -> float:
    sql = ("SELECT score from organisations_di_scores WHERE org_id = ? and score_type = 'ws_rank' "
           "order by timestamp desc LIMIT 1")
    cur = conn.cursor()
    cur.execute(sql, [org_id, ])
    rows = cur.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0][0]


def get_org_name_by_id(conn: sqlite3.Connection, org_id: int) -> str:
    sql = "SELECT name from organisations WHERE id = ?;"

    cur = conn.cursor()
    cur.execute(sql, [org_id, ])
    rows = cur.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0][0]


def get_mean_linkedin_followers(followers_data: dict) -> float:
    return mean([data['followers'] for data in followers_data])


def get_mean_ws_rank(conn: sqlite3.Connection) -> (str, float):
    sql = """SELECT timestamp, AVG(score) FROM organisations_di_scores 
            GROUP BY timestamp
            ORDER BY timestamp DESC
            LIMIT 1"""
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0]


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--data_folder", type=str,
                        default="./di_stats/",
                        help="Path to folder where the linkedin followers files to be processed are stored")

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
    files = glob.glob(args.data_folder + "/linkedin_stats_*.json")

    # Get the latest mean ws_rank across all companies (with a rank)
    (ws_rank_timestamp, mean_ws_rank) = get_mean_ws_rank(insight_db_conn)

    for file in files:
        timestamp = datetime.now()
        # Load the json file into memory as dict

        linkedin_stats = []
        with open(file) as f:
            linkedin_stats = json.load(f)

        # Get the mean followers across all companies in the file
        mean_linkedin_followers = get_mean_linkedin_followers(linkedin_stats)
        # Process each entry in the dict to compute the ws_rank then store this in the insights database
        for stats in linkedin_stats:
            org_id = stats["org_id"]
            org_name = get_org_name_by_id(insight_db_conn, org_id)
            linkedin_followers = stats['followers']
            ws_score = get_lastest_ws_rank_for_org(insight_db_conn, org_id)
            if ws_score is None:
                logger.warning(
                    f"Organisation {org_id} - {org_name} does not have a recent ws_score. Unable to compute the Digital Score")
                continue
            digital_score = compute_di_scores.get_digital_score(linkedin_followers, ws_score,
                                                                mean_linkedin_followers, mean_ws_rank)
            # Store the computed ws_rank in the insights database
            store_digital_score_for_org(insight_db_conn, org_id, timestamp, digital_score)
