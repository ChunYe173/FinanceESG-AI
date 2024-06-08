from corenlp.base_llama_langchain import BaseLlamaLangchain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
import logging


class ControversyDetectionQABased(BaseLlamaLangchain):
    """
    Class for detecting controversies in source documents based on retrieval augmented generation (RAG). 
    This procedure first retrieves text from the source documents based sentence transformer based embedding and then shows it to the llama based chatbot before asking
    it the final question. An example prompt is (from Langchain):
    
    ####
    Use the following pieces of context to answer the question at the end. If you don't know the answer, 
    just say that you don't know, don't try to make up an answer.
    
    ....retrieved content from documents....
    
    Question: Extract any contradictory or controversial statements about X company in the context text?
    Helpful Answer:
    ####
    For more information, please also look at this notebook 
    (https://dagshub.com/Omdena/Voy-Finance/src/main/src/tasks/NLP-tasks-exploration/controversy_detection_POC_llama7b/conterversy_detection.ipynb)
    """

    default_question_st = "Extract any contradictory or controversial statements about "
    default_question_end = " in the context text?"

    def __init__(self,
                 model_id: str = "Weyaxi/OpenHermes-2.5-neural-chat-7b-v3-1-7B",
                 hf_auth: str = ""):

        self.log = logging.getLogger("ControversyDetectionQABased")
        super().__init__(model_id, hf_auth)

    def make_extraction_chain(self, loaded_documents,
                              stop_list=['\nHuman:', '\n```\n'],
                              embedding_model="sentence-transformers/all-mpnet-base-v2"):

        """ Create a RAG extraction chain based on the loaded documents (Langchain based). 
        One can choose kind of stop word list they want to choose and whether 
        to log final input prompt."""

        llm = self.get_llm(stop_list)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)

        splits = text_splitter.split_documents(loaded_documents)
        model_kwargs = {"device": self.device}

        embeddings = HuggingFaceEmbeddings(model_name=embedding_model, model_kwargs=model_kwargs)

        vector_store = FAISS.from_documents(splits, embeddings)

        # allowing verbose shows what part of text was finally shown to the model.
        self.chain = ConversationalRetrievalChain.from_llm(llm,
                                                           vector_store.as_retriever(),
                                                           return_source_documents=True,
                                                           verbose=True)

    @staticmethod
    def format_answer(answer, show_source=False):
        '''Formatting the printed answer and showing 
        the source documents in case needed'''
        print("\033[1m" + answer["answer"] + "\033[0m")
        if show_source:
            print("For more information, please refer to documents with index")
            print([doc.metadata['index'] for doc in answer['source_documents']])

    def show_default_answer(self, company_name="Linde", show_source=True):
        '''Show the default answer. Executing this method shows 
        the default question.'''

        self.chat_history = []

        default_question = self.default_question_st + \
                           company_name + self.default_question_end

        print(f"The default question is:{default_question}")

        answer = self.chain({"question": default_question,
                             "chat_history": self.chat_history})
        self.chat_history.append((default_question,
                                  answer["answer"]))
        self.format_answer(answer, show_source)

    def question(self, question, show_source):
        '''Could be follow up question to default answer or starting question.'''

        # in case this is first question.
        if not hasattr(self, 'chat_history'):
            self.chat_history = []

        answer = self.chain({"question": question,
                             "chat_history": self.chat_history})

        self.chat_history.append([(question,
                                   answer["answer"])])

        self.format_answer(answer, show_source)
