import json
from json import JSONDecodeError
from typing import Dict

import pandas as pd
import requests

from news_content.gdelt_filters import Filters


class GdeltApiClient:
    """
    A simple API Client to interact with the GDELT API (version 2).
    """

    def __init__(self):
        self.supported_modes = ["artlist"]

    def get_article_list(self, filters: Filters) -> pd.DataFrame:
        """
        Attempts to retrieve a list of documents based on a filter criteria from the GDELT API.
        :param filters: The filters to apply to the query
        :return: A Pandas DataFrame containing the results of the query
        """
        # Get the list of articles
        articles = self._execute_query("artlist", filters.query_string)
        if isinstance(articles, dict) and  "articles" in articles:
            # return articles as a dataframe
            return pd.DataFrame(articles["articles"])
        else:
            # Return an empty dataframe
            return pd.DataFrame()

    def _execute_query(self, mode: str, query_string: str) -> Dict:
        """
        Private method to perform an API call to the GDELT API and return the articles found
        :param mode: The GDELT Query Mode - currently only "artlist" is supported
        :param query_string:  The query string to be added to the call to filter the documents.
        :return:
        """
        # Check the mode

        if mode.lower() not in self.supported_modes:
            raise ValueError(
                f"The mode '{mode} is not supported by this client. Supported modes are: {self.supported_modes}")

        # Run query via GDelt API
        headers = {"User-Agent": "Omdena GDELT Python API client"}
        request_url = f"https://api.gdeltproject.org/api/v2/doc/doc?{query_string}&mode={mode.lower()}&format=json"
        response = requests.get(request_url, headers)

        # Check for errors
        if response.status_code not in [200, 202]:
            raise RuntimeError(
                f"The GDELT API returns an unsuccessful Status Code ({response.status_code}). Message: {response.text}")

        return self.convert_to_json(response.content, max_tries=100)

    @staticmethod
    def convert_to_json(content, max_tries: int = 100) -> Dict:
        """
        Takes the JSON content from a GDELT API call and converts it into a Dictionary object.
        If the conversion fails (usually due to some unsupported character), the offending character is removed and
        the conversion repeated. This is repeated up to a maximum number of attempts.
        :param content: The JSON content to be parsed
        :param max_tries:  The maximum number of attempts to parse the data
        :return:
        """
        parsed_success = False
        cur_tries = 0
        result = {}
        while not parsed_success and cur_tries < max_tries:
            try:
                result = json.loads(content)
                parsed_success = True
            except JSONDecodeError as e:
                if cur_tries >= max_tries:
                    raise RuntimeError(f"Failed to decode the json content after {max_tries} attempts.")
                # Try to remove the undecodable character
                cur_tries += 1
                error_idx = int(e.pos)
                # Remove the undecodable char
                content_list = list(content)
                content_list[error_idx] = " "
                content = "".join(str(m) for m in content_list)
        return result
