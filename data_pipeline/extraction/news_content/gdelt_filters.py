from typing import Optional, List


class Filters:
    """
    Defines the Filters used when executing queries against the GDELT API
    This is a subset of the available filters and can be extended as needed
    """
    def __init__(self,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 max_records: int = 250,
                 keywords: List[str] = None,
                 source_languages: List[str] = None,
                 source_countries: List[str] = None,
                 themes: List[str] = None
                 ):
        """
        Constructs the filters of a call to the GDELT API
        Params
        -------
        :param start_date: the start date for the filter. Must be either YYYMMDD or YYYYMMDDHHMMSS
        :param end_date: the end date for the filter. Must be either YYYMMDD or YYYYMMDDHHMMSS
        :param max_records: the maximum number of records to download
        :param keywords: the list of keywords you want to search for
        :param source_languages: the list of languages you want to filter for (default is 'english')
        :param source_countries: the list of news article source countries you want to filter for (default is 'english')
        :param themes: the list of GDELT Themes you want to filter articles by such as "ENV_OIL" (see http://data.gdeltproject.org/api/v2/guides/LOOKUP-GKGTHEMES.TXT)
        """
        self.query_terms: List[str] = []
        self.query_params: List[str] = []

        if keywords and len(keywords) > 0:
            self.query_terms.append(self._keyword_to_string(keywords))

        if source_countries:
            self.query_terms.append(self._filter_clause_to_string("sourcecountry", source_countries))
        if source_languages:
            self.query_terms.append(self._filter_clause_to_string("sourcelang", source_languages))

        if themes:
            self.query_terms.append(self._filter_clause_to_string("theme", themes))

        # Start Date
        if start_date:
            if len(start_date) == 8:
                self.query_params.append(f"startdatetime={start_date + '000000'}")
            elif len(start_date) == 14:
                self.query_params.append(f"startdatetime={start_date}")

        # End Date
        if end_date:
            if len(start_date) == 8:
                self.query_params.append(f"enddatetime={end_date + '000000'}")
            elif len(start_date) == 14:
                self.query_params.append(f"enddatetime={end_date}")

        self.query_params.append(f"maxrecords={max_records}")

    @property
    def query_string(self) -> str:
        """Returns the query string based on the supplied filtered"""
        return "&".join([self.search_term_string, self.query_clause_string])

    @property
    def query_clause_string(self) -> str:
        """Returns the query parameters based on the supplied filtered"""
        if len(self.query_terms) > 0:
            return "&".join(self.query_params)
        else:
            return ""

    @property
    def search_term_string(self) -> str:
        """Returns the search and filter terms based on the supplied filtered"""
        if len(self.query_terms) > 0:
            return f'query={" ".join(self.query_terms)}'
        else:
            return ""

    @staticmethod
    def _filter_clause_to_string(name: str, terms: List[str]):
        """
        Private method to construct a Filter Clause term.
        Where multiple terms are provided, these will be OR'd together. GDELT does not support AND clauses
        :param name: the name of the filter clause (e.g. sourcelang, sourcecountries etc.)
        :param terms: The list of terms to be used in the filter clause
        :return: the filter terms correctly formatted as a string
        """
        if len(terms) == 0:
            return ""

        if len(terms) == 1:
            return f"{name}:{terms[0]}"

        return "(" + " OR ".join([f"{name}:{term}" for term in terms]) + ")"

    @staticmethod
    def _keyword_to_string(terms: List[str]):
        """
                Private method to construct a Keyword Search term.
                Where multiple terms are provided, these will be OR'd together. GDELT does not support AND clauses
                :param terms: The list of keywords to be used in the keywords clause
                :return: the keywords terms correctly formatted as a string
                """
        if len(terms) == 0:
            return ""

        if len(terms) == 1:
            return f'"{terms[0]}"'

        return "(" + " OR ".join([f'"{term}"' for term in terms]) + ") "
