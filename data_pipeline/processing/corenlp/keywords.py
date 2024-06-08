from typing import List
import textacy
from textacy import extract
import re
from transformers import pipeline
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
import numpy as np
from sentence_transformers import SentenceTransformer


class EsgKeywordExtractor:
    """
    Class to extract ESG related keywords from text
    """

    def __init__(self):
        model_name = "yiyanghkust/finbert-esg"
        self.spacy_en = textacy.load_spacy_lang("en_core_web_sm", disable=("parser,"))
        # Used to filter non-ESG related keywords
        self.esg_text_classifier = pipeline("text-classification", model=model_name)
        self.cluster_embeddings_model = SentenceTransformer('paraphrase-MiniLM-L12-v2')

    @staticmethod
    def _remove_ignores(doc: str, ignore_list: List[str]) -> str:
        """
        Removes a set of words or phrases from a document that we want to ignore
        """
        starts_re = "(^|\s|\W)"
        ends_re = "($|\s|\W)"

        # [^\w\s]+
        if ignore_list is None:
            return doc
        regex_replacements = [(f"{starts_re}{re.escape(item)}{ends_re}", " ") for item in ignore_list]
        for old, new in regex_replacements:
            doc = re.sub(old, new, doc, flags=re.IGNORECASE)

        return doc

    def remove_non_esg_keywords(self, keywords):
        """Uses FinBert to filter any non-ESG related keywords"""
        kw_list = []
        for kw in keywords:
            res = self.esg_text_classifier(kw)[0]
            if res['label'] != "None" and res['score'] >= 0.6:
                kw_list.append(kw)
        return kw_list

    def _get_keywords_textrank(self, text, ignore_list=None, top_n=10):
        """Uses Textacy to generate the keywords using Text Rank"""
        doc = textacy.make_spacy_doc(self._remove_ignores(text, ignore_list), lang="en_core_web_sm")
        top_terms = [kps for kps, weights in extract.keyterms.textrank(doc, normalize="lemma", topn=top_n)]
        textrank_terms = textacy.extract.utils.aggregate_term_variants(set(top_terms))
        # Construct list using one term from each aggregated set of terms
        textrank_terms = [term_set.pop() for term_set in textrank_terms]
        return textrank_terms

    def _get_clustered_labels(self, keywords: List[str], n_clusters: int = 3):
        num_clusters = min(len(keywords), n_clusters)
        # Compute embeddings
        embeddings = np.array(self.cluster_embeddings_model.encode(keywords, convert_to_tensor=True),
                              dtype=np.float32)
        # Cluster embeddings in vector space
        cluster_model = KMeans(n_clusters=n_clusters, n_init='auto')
        clustering = cluster_model.fit(embeddings)

        # Get embedding closest to the cluster centroid
        closest, _ = pairwise_distances_argmin_min(clustering.cluster_centers_, embeddings)
        return [keywords[idx] for idx in closest]

    def get_esg_keywords(self, text: str, ignore_terms: List[str] = None,
                         filter_non_esg_keywords: bool = True, top_n: int = 10) -> List[str]:
        keywords = self._get_keywords_textrank(text, ignore_terms, top_n=top_n)
        # Filter non-ESG keywords if required
        if filter_non_esg_keywords:
            keywords = self.remove_non_esg_keywords(keywords)

        # Cluster keywords to remove duplication
        if len(keywords) >= 3:
            keywords = self._get_clustered_labels(keywords)

        return keywords
