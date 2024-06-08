from typing import List

import pandas as pd
from newspaper import Article, ArticleException

from news_content.gdelt_api_client import GdeltApiClient
from news_content.gdelt_filters import Filters


class ArticleExtractor:
    def __init__(self):
        self.gdelt_client = GdeltApiClient()

    def get_articles(self,
                     keywords: List[str] = None,
                     languages: List[str] = None,
                     source_countries: List[str] = None,
                     gdelt_themes: List[str] = None,
                     start_date: str = None,
                     end_date: str = None,
                     max_records=100
                     ):
        # Call GDELT API to extract articles
        if not languages:
            languages = ["english"]

        if len(keywords) > 70:
            keywords = keywords[:70]
        filters = Filters(
            start_date=start_date,
            end_date=end_date,
            max_records=max_records,
            keywords=keywords,
            source_languages=languages,
            source_countries=source_countries,
            themes=gdelt_themes
        )
        articles = self.gdelt_client.get_article_list(filters=filters)
        if articles.shape[0] == 0:
            return pd.DataFrame()
        urls = list(articles['url'])

        # download the articles
        articles["content"] = self._extract_articles(urls)

        return articles

    @staticmethod
    def _extract_articles(urls: List[str]) -> List[str]:
        articles: List[str] = []
        for url in urls:
            try:
                article = Article(url)
                article.download()
                article.parse()
                article_text = article.text
                articles.append(article_text)
            except ArticleException as e:
                print(f"Failed to download article from {url}.\nException Message: {e}")
                articles.append("")

        return articles
