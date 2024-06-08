import os

os.environ["OMP_NUM_THREADS"] = '1'  # Required to avoid memory leak on Windows
import datetime
import glob

import sqlite3
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import logging
import argparse

from corenlp.classification import EsgTextClassification
from corenlp.esg_sentiment_analysis import EsgSentimentAnalysis
from corenlp.keywords import EsgKeywordExtractor
from corenlp.named_entity_extraction import EntityExtractor

logger = logging.getLogger("news_text_insights")
logger.info("Preparing models")
esg_sent_classifier = EsgSentimentAnalysis(lazy_load=False)
esg_classifier = EsgTextClassification(lazy_load=False)
esg_keywords_extractor = EsgKeywordExtractor()
entity_extractor = EntityExtractor()
logger.info("Models loaded")


def get_org_id_by_name(conn, company_name):
    sql = "SELECT id FROM organisations where LOWER(name) = ?"
    cur = conn.cursor()
    cur.execute(sql, (company_name.lower(),))
    rows = cur.fetchall()
    cur.close()
    if len(rows) == 0:
        return None
    else:
        return rows[0][0]


def insert_doc_info(conn, company_id, broad_cat, pub_date, source_url, source_country, doc_type, sentiment):
    sql = """ INSERT INTO documents(org_id, esg_category, timestamp, source_url, source_country,doc_type , sentiment)
                VALUES(?, ?, ?, ?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [company_id, broad_cat, pub_date, source_url, source_country, doc_type, sentiment])
    conn.commit()
    return cur.lastrowid


def insert_doc_parts_info(conn, doc_id, part_idx, content, topic):
    sql = """ INSERT INTO document_parts(document_id, document_part_idx, document_part_content, esg_category)
                    VALUES(?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [doc_id, part_idx, content, topic])
    conn.commit()
    return cur.lastrowid


def insert_doc_part_sentiment_info(conn: sqlite3.Connection, doc_id: int, part_idx: int, sentiment: float):
    sql = """ INSERT INTO document_part_scores(document_id, document_part_idx, score_type, score)
                        VALUES(?, ?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [doc_id, part_idx, "sentiment", sentiment])
    conn.commit()
    return cur.lastrowid


def insert_doc_entities_info(conn, doc_id, entity_label, entity_type):
    sql = """ INSERT INTO document_entities(document_id, entity, entity_type)
                        VALUES(?, ?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [doc_id, entity_label, entity_type])
    conn.commit()
    return cur.lastrowid


def insert_doc_keywords_info(conn, doc_id, keyword):
    sql = """ INSERT INTO document_keywords(document_id, keyword)
                            VALUES(?, ?)"""
    cur = conn.cursor()
    cur.execute(sql, [doc_id, keyword])
    conn.commit()
    return cur.lastrowid


def rescale_sentiments(sentiments):
    """
    Rescales the probability values for the 3 sentiments so that we have a single value in the range -1 to 1 where
        - values close to +1 indicate a high probability of a Positive sentiment
        - values close to -1 indicate a high probability of a Negative sentiment
        - values close to 0 indicate a high probability of a Neutral sentiment
    """
    rescaled_sents = []

    def rescale_sentiment(sentiment):
        sentiment.sort(key=lambda a: a[1], reverse=True)
        sent_label = sentiment[0][0].lower()
        sent_prob = sentiment[0][1] * (2.0 / 3.0)  # Normalise into a range between 0 to 2/3

        if sent_label == "positive":
            # Most likely Positive
            # Shift to range +1/3 to 1 with 1 being definitely positive
            return (1.0 / 3.0) + sent_prob
        elif sent_label == "negative":
            # Most likely Negative
            # Shift to range -1/3 to -1 with -1 being definitely negative
            return (-1.0 / 3.0) - sent_prob
        else:
            # Most likely Neutral
            # This is more complex since we want the definitely neutral to be 0
            # But less neutral to move closer to either -1 or +1 depending upon the next most likely score
            # So we shift the range to -1/3 to 0 and then check the second most likely answer and
            # if it is positive multiply by -1 to give a value in the range 0 to 1/3 or leave as range -1/3 to 0
            # Shift to range -1/3 to +1/3 with 0 being definitely neutral
            sent_prob = (sent_prob / 2.0) - (1.0 / 3.0)
            if sentiment[1][0].lower() == "positive":
                sent_prob = sent_prob * (-1.0)
            return sent_prob

    for s in sentiments:
        rescaled_sents.append(rescale_sentiment(s))

    return rescaled_sents


def process_content(company_name: str, content: str):
    # Store document level information
    # Chunk content into paragraphs and run sentiment on ESG Parts and store parts
    parts = [part.strip() for part in content.split('\n') if len(part.strip()) > 0]
    esg_topics = esg_classifier.get_esg_topic(parts)
    esg_sents = rescale_sentiments(esg_sent_classifier.get_esg_sentiment(parts))

    try:
        doc_parts = [{"content": part, "topic": topic, "sentiment": sentiment} for part, topic, sentiment in
                     zip(parts, esg_topics, esg_sents)]
    except TypeError as e:
        print(e)

    doc_sent = np.mean(esg_sents)

    # Extract Entities and store entities
    entities = entity_extractor.extract_entities(content)

    # Keyword Extraction and store keywords
    ignore_terms = set()
    ignore_terms.add(company_name)
    for entity in entities.values():
        ignore_terms.update(entity)
    keywords = esg_keywords_extractor.get_esg_keywords(content, ignore_terms=list(ignore_terms), top_n=20)

    # ToDo: Currently unable to integrate the LLM based Controversy Detection or Relationship Extraction models
    #   These appear to require CUDA/GPU to run inference which is not available in most of the developer environments
    #   and may not be available in the deployment environment
    # Detect Controversy and store controversy (if detected)
    # Extract Relationship triplets

    return {"doc_sentiment": doc_sent, "doc_parts": doc_parts, "keywords": keywords, "entities": entities}


def process_gdelt_articles(data_folder: str, insights_db_conn: sqlite3.Connection):
    """
    Function to process the files generated by the GDELT Article Downloader script.
    These are CSV files that contain metadata about the articles and the article content.
    These files are .csv fies and the filename is of the form <company_name>_<download_timestamp>.csv
    """
    logger.info("Processing data from GDELT database")

    # Process CSV files only
    files = glob.glob(data_folder + "/*.csv")

    for data_file in files:
        file_name = Path(data_file).stem
        company_name = file_name.split('_')[1]
        company_id = file_name.split('_')[0]

        # Load file into dataframe
        df = pd.read_csv(data_file)
        # Process each row
        num_articles = df.shape[0]
        logger.info(f"Processing articles for {company_name} - {num_articles} articles found")
        for idx in range(num_articles):
            logger.info(f"Process article {idx + 1} of {num_articles}")
            # If the row has content then process otherwise skip
            content = str(df.iloc[idx]['content']).strip()
            if len(content) == 0:
                logger.info("No content found for article")
                continue
            # get the content and check if it is ESG related
            esg_category = esg_classifier.is_esg_related(content)
            # If the top classification is None then skip
            broad_cat = esg_category[0][0]['label'].strip()
            if broad_cat.lower() == "none":
                logger.info("Content is not ESG Related")
                continue
            # Extract article metadata
            pub_date = datetime.strptime(df.iloc[idx]['seendate'], "%Y%m%dT%H%M%SZ")
            source_country = df.iloc[idx]['sourcecountry']
            source_url = df.iloc[idx]['url']
            doc_type = "news"

            # Extract insights from the article content
            content_info = process_content(company_name, content)

            # Store the metadata and extracted insights into the insights database
            doc_id = insert_doc_info(insights_db_conn, company_id, broad_cat, pub_date, source_url, source_country,
                                     doc_type, content_info["doc_sentiment"])

            for part_idx, part in enumerate(content_info["doc_parts"]):
                part_content = part["content"]
                topic = part["topic"][0]['label']
                sentiment = part["sentiment"]

                insert_doc_parts_info(insights_db_conn, doc_id, part_idx, part_content, topic)
                insert_doc_part_sentiment_info(insights_db_conn, doc_id, part_idx, sentiment)

            for entity_type in content_info["entities"].keys():
                for entity_label in content_info["entities"][entity_type]:
                    insert_doc_entities_info(insights_db_conn, doc_id, entity_label, entity_type)
            for keyword in content_info["keywords"]:
                insert_doc_keywords_info(insights_db_conn, doc_id, keyword)

    logger.info("Processing Complete")


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--data_folder", type=str,
                        default="./news_downloads",
                        help="Path to folder where the data files to be processed are stored")
    parser.add_argument("--source", type=str,
                        default="gdelt",
                        help="The source of the data to be processed. Default is GDELT")
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

    insights_db_conn = sqlite3.connect(args.insight_db)

    # At the moment, we only support gdelt as a news source but we could add additional sources
    if args.source.lower().strip() == "gdelt":
        process_gdelt_articles(args.data_folder, insights_db_conn)
    logger.info("Processing Complete")
