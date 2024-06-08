# `%%writefile base_llama_langchain.py
import torch
from torch import cuda, bfloat16
import transformers
from transformers import StoppingCriteria, StoppingCriteriaList
from langchain.llms import HuggingFacePipeline


class BaseLlamaLangchain:
    """
    Base class for creating a Lllama model based chain inherited by 
    both EsgTripletExtraction and ESGConterversyDetection.
    """

    def __init__(self, model_id, hf_auth):

        self.model_id = model_id
        self.hf_auth = hf_auth

        self.device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

        model_config = transformers.AutoConfig.from_pretrained(
            model_id,
            use_auth_token=hf_auth
        )

        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            config=model_config,
            load_in_4bit=True,
            device_map='auto',
            use_auth_token=hf_auth
        )

        # enable evaluation mode to allow model inference
        self.model.eval()

        # log message
        model_loaded_msg = f"Model loaded on {self.device}"
        self.log.info(model_loaded_msg)

    def get_stopping_criteria(self, tokenizer, stop_list):

        """ Returns a stopping criteria object required by hugging face pipeline object"""

        stop_token_ids = [tokenizer(x)['input_ids'] for x in stop_list]
        # load them on the device
        stop_token_ids = [torch.LongTensor(x).to(self.device) for x in stop_token_ids]

        # define custom stopping criteria object
        class StopOnTokens(StoppingCriteria):
            def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
                for stop_ids in stop_token_ids:
                    if torch.eq(input_ids[0][-len(stop_ids):], stop_ids).all():
                        return True
                return False

        return StoppingCriteriaList([StopOnTokens()])

    def get_llm(self, stop_list):

        """ Create a langchain llm based on transformer pipeline."""

        tokenizer = transformers.AutoTokenizer.from_pretrained(
            self.model_id,
            use_auth_token=self.hf_auth
        )

        stopping_criteria = self.get_stopping_criteria(tokenizer, stop_list)

        generate_text = transformers.pipeline(
            model=self.model,
            tokenizer=tokenizer,
            return_full_text=True,  # langchain expects the full text
            task='text-generation',
            temperature=0.1,
            max_new_tokens=512,
            # we pass model parameters here too
            stopping_criteria=stopping_criteria,  # without this model rambles during chat
            repetition_penalty=1.1)

        return HuggingFacePipeline(pipeline=generate_text)
