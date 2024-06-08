"""
Script to process downloaded Sustainability reports and run the Greenwashing Detection model against the extracted text
to detect any claims that indicate an Organization's attempt to greenwash

The script will read in the Sustainability Reports and extract the raw text content from the PDF
The content will be chunked and the greenwashing model run against each chunk to detect any claims that appear to be attempts at greenwashing
The script will then store the content (as chunks) in the insights database along with the greenwashing model results
"""
import glob
import logging
import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from file_processing import sustainability_reports
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from greenwashing import greenwashing
from corenlp.classification import EsgTextClassification

logger = logging.getLogger("gw_detection")


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


def insert_doc_info(conn, company_id, pub_date, doc_type):
    sql = """ INSERT INTO documents(org_id, timestamp, doc_type)
                VALUES(?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [company_id, pub_date, doc_type])
    conn.commit()
    return cur.lastrowid


def insert_doc_parts_info(conn, doc_id, part_idx, content, esg_topic):
    sql = """ INSERT INTO document_parts(document_id, document_part_idx, document_part_content, esg_category)
                    VALUES(?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [doc_id, part_idx, content, esg_topic])
    conn.commit()
    return cur.lastrowid


def insert_doc_part_gw_info(conn: sqlite3.Connection, doc_id: int, part_idx: int, gw_score: float):
    sql = """ INSERT INTO document_part_scores(document_id, document_part_idx, score_type, score)
                        VALUES(?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [doc_id, part_idx, "greenwashing", gw_score])
    conn.commit()
    return cur.lastrowid


def store_gw_model_to_insights(conn, org_id, report_parts, part_topics, model_scores):
    # Add the document level information
    pub_date = datetime.now().strftime('%Y%m%d%H%M%S')
    doc_id = insert_doc_info(conn, org_id, pub_date, "sustainability_report")

    # Add the document parts level information
    for idx, (content, topic, score) in enumerate(zip(report_parts, part_topics, model_scores)):
        insert_doc_parts_info(conn, doc_id, idx, content, topic)
        insert_doc_part_gw_info(conn, doc_id, idx, score)


def get_report_part_esg_topic(esg_classifier, report_parts) -> list[str]:
    batch_size = 50

    def chunk(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    batches = chunk(report_parts, batch_size)
    part_topics = []
    for batch in batches:
        part_topics += esg_classifier.get_esg_topic(batch)

    part_topics = [topic[0]['label'] if topic[0]['prob'] > 0.5 else "Non-ESG" for topic in part_topics]
    return part_topics


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)
    default_gw_model_name = "tushar27/Env-Claims"

    parser = argparse.ArgumentParser()
    parser.add_argument("--data_folder", type=str,
                        default="./sustainability_reports/",
                        help="Path to folder where the sustainability reports pdf files to be processed are stored")

    parser.add_argument("--insight_db", type=str,
                        default="./insights.db",
                        help="The path to the insights database file")

    parser.add_argument("--gw_model_name", type=str,
                        default=default_gw_model_name,
                        help=f"The name of the HuggingFace model to load for Greenwashing detection. Default is '{default_gw_model_name}'")

    args = parser.parse_args()

    if args.data_folder is None or not os.path.exists(args.data_folder):
        logger.error(f"The path to the data could not be found or is not accessible. Path was {args.data_folder}")
        exit()

    if args.insight_db is None or not os.path.exists(args.insight_db):
        raise RuntimeError(
            f"The Insights database was not found or is not accessible. Path provided was '{args.insight_db}'")

    logger.info(f"Loading Greenwashing Detection Model from HuggingFace ({args.gw_model_name})")
    gw_tokenizer = AutoTokenizer.from_pretrained(args.gw_model_name)
    gw_model = AutoModelForSequenceClassification.from_pretrained(args.gw_model_name)

    logger.info("Loading ESG Topic Classification Model from HuggingFace")
    esg_classifier = EsgTextClassification()

    insights_db_conn = sqlite3.connect(args.insight_db)

    # Process Sustainability Reports to detect claims
    files = glob.glob(args.data_folder + "/*.pdf")

    for data_file in files:
        file_name = Path(data_file).stem
        org_id, org_name = find_org_by_alias(insights_db_conn, Path(data_file).stem)
        if org_id is not None:
            logger.info(f"Matched report {file_name} to organization {org_id} - {org_name}")
        else:
            logger.warning(f"Failed to match the report {file_name} to an organization.")
            continue

        report_parts = sustainability_reports.extract_content_from_pdf(data_file)

        part_topics = get_report_part_esg_topic(esg_classifier, report_parts)

        model_scores = greenwashing.run_inference_on_text(gw_tokenizer, gw_model, report_parts)
        store_gw_model_to_insights(insights_db_conn, org_id, report_parts, part_topics, model_scores)

    logger.info("Processing Complete")
