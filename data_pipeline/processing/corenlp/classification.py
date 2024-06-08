from typing import List
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging
import torch


class EsgTextClassification:
    """
    Performs classification of texts into ESG related Categories
    The class uses a set of HuggingFace Transformer models to perform the classification.
    These models are lazy loaded (i.e. they are only loaded if used) and consequently the first call to classify
    text will take some time to complete but subsequent calls will be quicker since the model is already loaded.
    """

    def __init__(self, lazy_load=True):
        self.log = logging.getLogger("EsgTextClassification")

        # Model that is used to perform course grain document classification (ESG  or not)
        self.esg_course_classifier_model_name = "yiyanghkust/finbert-esg"
        self.esg_course_classifier_tokenizer = None
        self.esg_course_classifier_model = None

        # FinBert-ESG-9 categories model to classify ESG documents into one of 9 categories
        self.esg_fine_classifier_model_name = "yiyanghkust/finbert-esg-9-categories"
        self.esg_fine_classifier_tokenizer = None
        self.esg_fine_classifier_model = None

        if not lazy_load:
            self._load_esg_course_classifier()
            self._load_esg_fine_classifier()

    def _load_esg_course_classifier(self):
        self.log.info("Loading ESG Course Grained Text Classifier")
        self.esg_course_classifier_tokenizer = AutoTokenizer.from_pretrained(self.esg_course_classifier_model_name)
        self.esg_course_classifier_model = AutoModelForSequenceClassification.from_pretrained(
            self.esg_course_classifier_model_name)

    @staticmethod
    def _order_and_label(logits, labels) -> List:
        ordered_preds = []
        for res in logits:
            sample_preds = []
            for idx, prob in enumerate(res):
                sample_preds.append({"label": labels[idx], "prob": prob.item()})
            ordered_preds.append(sorted(sample_preds, key=lambda x: x['prob'], reverse=True))
        return ordered_preds

    def _course_classifier_post_processing(self, logits) -> List:
        return self._order_and_label(logits, self.esg_course_classifier_model.config.id2label)

    def _fine_classifier_post_processing(self, logits):
        return (self._order_and_label(logits, self.esg_fine_classifier_model.config.id2label))

    def _load_esg_fine_classifier(self):
        self.log.info("Loading ESG Fine Grained Text Classifier")
        self.esg_fine_classifier_tokenizer = AutoTokenizer.from_pretrained(self.esg_fine_classifier_model_name)
        self.esg_fine_classifier_model = AutoModelForSequenceClassification.from_pretrained(
            self.esg_fine_classifier_model_name)

    def _do_inference(self, texts, tokenizer, model):
        """ Performs inference using a huggingface model and tokenizer and returns the predictions"""

        # Normally for the tokenizer you don't need to specify the max length since it is defined for tokenizer
        # but the Finbert models, this has not been set but the BERT models only accepts 512
        tok_inputs = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors='pt')
        outputs = model(**tok_inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        return predictions

    def is_esg_related(self, text: str) -> List:
        """
        Function to categorise text into one of 4 categories:
            - Environmental
            - Social
            - Governance
            - None
        Params:
            text: a string or list of strings to be classified. Each string is classified seperately.

        Returns:
            List containing the classification for each input text.
            Each classification is an ordered list of dictionary objects (Label and Score).

        Note: the model has a 512 token limit and so texts longer than 512 will be truncated during the
         classification process
       """

        if self.esg_course_classifier_tokenizer is None or self.esg_course_classifier_model is None:
            self._load_esg_course_classifier()
        return self._course_classifier_post_processing(
            self._do_inference(text, self.esg_course_classifier_tokenizer, self.esg_course_classifier_model))

    def get_esg_topic(self, text) -> List:
        """
        Function to categorise text into one of a set of ESG Topics.
        The current class uses the FinBert-ESG-9-Categories transformer so for each input text will an order list of
        topics with the associated probability.
        The 9 topics are:
            - Climate Change
            - Pollution & Waste
            - Corporate Governance
            - Natural Capital
            - Product Liability
            - Human Capital
            - Business Ethics & Values
            - Community Relations
            - Non-ESG

        Params:
            text: a string or list of strings to be classified. Each string is classified separately.
            This method is best called on sentences or paragraphs containing related content
            (e.g. all sentences relate to Pollution) - otherwise, the strength of the signal for the ESG topic is reduced.

        Returns:
            List containing the classification for each input text.
            Each classification is an ordered list of dictionary objects (Label and Score).

        Note: the model has a 512 token limit and so texts longer than 512 will be truncated during the
         classification process
       """

        if self.esg_fine_classifier_tokenizer is None or self.esg_fine_classifier_model is None:
            self._load_esg_fine_classifier()
        return self._fine_classifier_post_processing(
            self._do_inference(text, self.esg_fine_classifier_tokenizer, self.esg_fine_classifier_model))
