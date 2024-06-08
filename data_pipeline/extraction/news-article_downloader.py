import argparse
import datetime
import logging
import os
import sqlite3
import time
from utils import org_utils

from news_content.article_extractor import ArticleExtractor
import pandas as pd

logger = logging.getLogger("news_article_downloader")


def save_articles(company_id: int, company_name: str, articles_df: pd.DataFrame, save_folder: str):
    company_name = company_name.replace(".", " ").replace("  ", " ").strip()
    file_path = os.path.join(save_folder, f"{company_id}_{company_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
    articles_df.to_csv(file_path)


def download_company_news_articles(companies: list[(int, str)], start_date: str, end_date: str, output_dir: str):
    logger.info(f"Starting Search and Download for articles between '{start_date}' and '{end_date}'")
    logger.info(f"Output stored in {output_dir}")
    extractor = ArticleExtractor()

    company_has_news = []

    consecutive_fails = 0

    for idx, (company_id, company) in enumerate(companies):
        logger.info(f"Company: {company} ({idx + 1}/{len(companies)})")
        has_articles = False
        try:
            company = company.strip().replace("  ", " ")
            content = extractor.get_articles(keywords=[company],
                                             languages=None,
                                             source_countries=None,
                                             gdelt_themes=None,
                                             start_date=start_date,
                                             end_date=end_date,
                                             max_records=500)
            has_articles = (len(content.index) > 0)

            if has_articles:
                save_articles(company_id, company, content, output_dir)
            consecutive_fails = 0
        except Exception as e:
            logger.info("Failed to retrieve")
            consecutive_fails += 1
            if consecutive_fails > 10:
                break
            time.sleep(6)
        finally:
            company_has_news.append(has_articles)
            if has_articles:
                logger.info("\tHas News")
            else:
                logger.info("\tNo News found")
            # GDELT has rate limiting, so we need to pause to avoid hitting the limit
            time.sleep(6)

    if len(company_has_news) < len(companies):
        companies = companies[:len(company_has_news)]

    out_df = pd.DataFrame({"name": companies, "has_gdelt_news": company_has_news})
    out_df.set_index("name", inplace=True)
    out_df.to_csv("./company_news_gdelt.csv")


if __name__ == '__main__':
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--insights_db_path", type=str, default="./insights.db", help="Path to the insights database")
    parser.add_argument("--out_folder", type=str, default="./news_downloads",
                        help="Path to folder where you want the downloaded documents to be stored")
    parser.add_argument("--start_date",
                        type=lambda s: datetime.date.strptime("%Y%m%d"),
                        default=datetime.datetime.now() - datetime.timedelta(1),
                        help="The earliest date for news articles")
    parser.add_argument("--end_date",
                        type=lambda s: datetime.date.strptime("%Y%m%d"),
                        default=datetime.datetime.now(),
                        help="The latest date for news articles")
    args = parser.parse_args()
    if not os.path.exists(args.out_folder):
        os.mkdir(args.out_folder)

    if not os.path.exists(args.insights_db_path):
        raise RuntimeError(f"The Insights database could not be found at {args.insights_db_path}")

    insights_db_conn = sqlite3.connect(args.insights_db_path)
    company_names = org_utils.get_company_names(insights_db_conn)

    download_company_news_articles(company_names,
                                   args.start_date.strftime("%Y%m%d"),
                                   args.end_date.strftime("%Y%m%d"),
                                   args.out_folder)
