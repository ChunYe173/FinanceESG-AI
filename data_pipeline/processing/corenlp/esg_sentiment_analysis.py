import torch
import logging
from typing import List
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class EsgSentimentAnalysis:
    """
    Performs sentiment analysis on esg texts
    The class uses a HuggingFace Transformer models to perform the sentiment analysis.
    """

    def __init__(self, lazy_load=True):
        self.log = logging.getLogger("EsgTextSentimentAnalysis")

        # HuggingFace Transformer model
        self.esg_sentiment_analysis_model_name = "TrajanovRisto/bert-esg"
        self.esg_sentiment_analysis_tokenizer = None
        self.esg_sentiment_analysis_model = None

        if not lazy_load:
            self._load_esg_sentiment_analysis()

    def _load_esg_sentiment_analysis(self):
        # Load the model
        self.log.info("Loading ESG Sentiment Analysis Model")
        self.esg_sentiment_analysis_tokenizer = AutoTokenizer.from_pretrained(self.esg_sentiment_analysis_model_name)
        self.esg_sentiment_analysis_model = AutoModelForSequenceClassification.from_pretrained(self.esg_sentiment_analysis_model_name)

    @staticmethod
    def _order_and_label(logits, labels) -> List:
        # Output the sentiment and change the output from 9 labels into 3 labels (Positive, Neutral, Negative) and the probability of each labels
        ordered_preds = []
        for res in logits:
            sample_preds = [{'Positive': 0.0, 'Neutral': 0.0, 'Negative': 0.0}]
            for idx, prob in enumerate(res):
                detailed_label = labels[idx]

                if 'Positive' in detailed_label:
                    sample_preds[0]['Positive'] += prob.item()
                elif 'Neutral' in detailed_label:
                    sample_preds[0]['Neutral'] += prob.item()
                elif 'Negative' in detailed_label:
                    sample_preds[0]['Negative'] += prob.item()

            ordered_preds.append(sorted(sample_preds[0].items(), key=lambda x: x[1], reverse=True))
        return ordered_preds

    def _sentiment_analysis_post_processing(self, logits) -> List:
        return self._order_and_label(logits, self.esg_sentiment_analysis_model.config.id2label)
    
    def _do_inference(self, texts, tokenizer, model):
        """ Performs inference using a huggingface model and tokenizer and returns the predictions"""

        tok_inputs = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors='pt')
        outputs = model(**tok_inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        return predictions
    
    def get_esg_sentiment(self, text: str) -> List:
        """
        Function to categorise text into one of 3 sentiments:
            - Positive
            - Neutral
            - Negative
        Params:
            text: a string or list of strings to be analyze.

        Returns:
            List containing the sentiment for each input text.
            Each sentiment is an ordered list of dictionary objects (Sentiments and Scores).
       """

        if self.esg_sentiment_analysis_tokenizer is None or self.esg_sentiment_analysis_model is None:
            self._load_esg_sentiment_analysis()
        return self._sentiment_analysis_post_processing(
            self._do_inference(text, self.esg_sentiment_analysis_tokenizer, self.esg_sentiment_analysis_model))