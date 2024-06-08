from typing import List, Dict
import logging
from kor import create_extraction_chain
from corenlp.triplet_extraction_schema import schema
from corenlp.base_llama_langchain import BaseLlamaLangchain


def return_emptystring_or_value(dic, key1, key2=None):
    """ A helper function for post processing
    function of EsgTripletExtraction."""

    if key2 is None:
        return dic[key1] if key1 in dic else ""
    else:
        return dic[key1][key2] if key1 in dic and key2 in dic[key1] else ""


class EsgTripletExtraction(BaseLlamaLangchain):
    """
    Class for extracting triplets in the following way:
    
    Input: In accordance with our ambitious goal, the water withdrawal of the data center decreased remarkably from 3.874 million litres to 2.367 million litres across the past three years.
    
    Output: {"esg_category": "Water", "predicate": "Reduction of", "object": "The water withdrawal of the data center by 1.507 million litres"}
    
    It extracts categories of prepared using six distinct ESG data providers Sustainalytics, S&P Global, Refinitiv, Moody’s ESG, Morgan Stanley Capital International-MSCI, and MSCI-KLD. A predicate to this category and object of action taken with respect to the category. 
    
    The prompt structure and model used are basically followed from this work:
    https://arxiv.org/pdf/2310.05628.pdf
    """

    def __init__(self, model_id="TheBloke/wizardLM-7B-HF", hf_auth=""):
        self.log = logging.getLogger("EsgTripletExtraction")
        super().__init__(model_id, hf_auth)

    def make_extraction_chain(self, stop_list=['\nHuman:', '\n```\n'],
                              log_final_input_prompt=False):

        """ Create an extraction chain based on prompt created by schema mentioned in triplet_extraction_schema module. One can choose kind of stop word list they want to choose and whether to log final input prompt."""
        llm = self.get_llm(stop_list)

        self.chain = create_extraction_chain(llm, schema, encoder_or_encoder_class='json')

        if log_final_input_prompt:
            self.log.info("*" * 100 + "\n" + "*" * 100 + "\n" + "*" * 100 + "\n",
                          self.chain.prompt.format_prompt(text="[user input]").to_string(),
                          "\n" + "*" * 100 + "\n" + "*" * 100 + "\n" + "*" * 100, "\n")

    def post_process_single_output(self, output):

        """ Post processing a single output from the chat model. This requires removing noisy output from the model and returning empty dictionary in that case."""
        processed_out = {}
        data_extracted = output['text']['data']['esg_actions'] if len(output["text"]["data"]) else {}
        transfer_dict = data_extracted[0] if len(data_extracted) else {}

        processed_out["esg_category"] = return_emptystring_or_value(transfer_dict, "esg_category")
        processed_out["predicate"] = return_emptystring_or_value(transfer_dict, "predicate")
        processed_out["object"] = return_emptystring_or_value(transfer_dict, "object")

        return processed_out

    def post_processing(self, output):

        """ Checks whether an output is string (single entry) or list(multiple enteries)."""
        if isinstance(output, dict):
            return self.post_process_single_output(output)

        if isinstance(output, list):
            return [self.post_process_single_output(out) for out in output]

    def extract_triplets(self, input_text, batch_size=None) -> List[Dict]:
        """
        Function for extracting triplets.

        Params:
            input_text: A single entry of text or list or any interable object of text enteries.
            batch_size : If multiple enteries are input, then batch size to perform inference.
            
        Returns:
            Dictionary or list of triplets extracted.
       """
        if batch_size is None:
            output = self.chain.run({"text": input_text})
            # recreating the dictionary format to match chain.apply
            return self.post_processing({"text": output})

        else:
            final_out = []
            for idx in range(len(input_text) // batch_size):
                batch = input_text[idx * batch_size:(idx + 1) * batch_size]
                batch_out = self.chain.apply([{"text": txt} for txt in batch])
                batch_out = self.post_processing(batch_out)
                final_out += batch_out

            return final_out
