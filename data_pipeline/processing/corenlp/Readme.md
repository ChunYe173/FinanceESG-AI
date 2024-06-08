# CoreNLP package
This package contains a set of classes and methods that perform core NLP processing that are tailored (as far as possible) to ESG Content.
The core capabilities include:

| Task                                | Purpose                                                                                                                                                                                                                   |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| __Document Classification__         | Given a document (text) the model will predict whether the text is ESG Related or not. This can be used to perform an initial filtering of documents and text so that non-ESG related texts can be discarded.             |                                                              |
| __Named Entity Extraction__         | Given some text, the model will attempt to extract a set of Entities from the text. This is used for knowledge extraction and the linking of Entities in the article to the organizational entities that we are tracking. |
| __Sentiment Analysis__              | Given some text, the model will attempt to provide a sentiment score for the text. This is used to understand media and social perceptions about the organizations we are tracking                                        |                                           |
| __Relationship/Triplet Extraction__ | Given some text, the model will attempt to extract relationships between the different entities. This is used to create our knowledge graph about organizations we are tracking                                           |
| __Controversy Extraction__          | Given some documents related to a company, the model will attempt to extract controversial or contradictory statements related to it from the documents                                                                   |
|

## Dependencies
The dependencies for the CoreNLP package are listed in the ```requirements.txt``` file for this package.

## Usage
The following sections provide usage instructions for each of these tasks.

### ESG Document Classification
The ```EsgTextClassification``` class is responsible for performing classification of text into ESG Topics. 
The class currently uses 2 Transformer models to perform classification at two levels:
1. Broad categorisation into Environmental, Social, Governance or Non-ESG. This is typically used to determine if a document is ESG related or not.
2. Finer categorisation into 8 ESG topics and a Non-ESG topic. This is typically used at a sentence or paragraph level to tag parts of a document by ESG category.

The models used are
* https://huggingface.co/yiyanghkust/finbert-esg
* https://huggingface.co/yiyanghkust/finbert-esg-9-categories

These models have a maximum context length of 512 tokens and during categorisation the models will ignore text after the context length is reached.
These models as Lazy Loaded, this means the models are not instantiated when the Class is instantiated. 
Instead, the models are loaded when they are first used; this means that the first call to classify a document will take longer but subsequent models.
This can be overriden in the constructor by adding the parameter ```lazy_load=False``` and will result in a slower class initialisation.

The following is an example usage for the two methods of classification

```python
from corenlp.classification import EsgTextClassification

classifier = EsgTextClassification()

press_release = "Once complete, the installation will generate enough renewable energy annually to power the " \
                 "equivalent of 34,000 homes. The project is expected to create around 300 jobs during construction " \
                 "and provide more than $25 million in tax revenue over the first 25 years of the project’s life."

broad_category = classifier.is_esg_related(press_release)

esg_topic = classifier.get_esg_topic(press_release)
```
For the above example, the ```broad_category``` would be
```python
[[
    {'label': 'Environmental', 'prob': 0.9794146418571472}, 
    {'label': 'Social', 'prob': 0.012545015662908554}, 
    {'label': 'None', 'prob': 0.005898956209421158}, 
    {'label': 'Governance', 'prob': 0.002141388365998864}
]]
```
The ```esg_topic``` output would be
```python
[[
    {'label': 'Climate Change', 'prob': 0.9944826364517212},
    {'label': 'Community Relations', 'prob': 0.001436759950593114}, 
    {'label': 'Natural Capital', 'prob': 0.001060737413354218}, 
    {'label': 'Pollution & Waste', 'prob': 0.0007274228264577687}, 
    {'label': 'Product Liability', 'prob': 0.0006597923347726464}, 
    {'label': 'Corporate Governance', 'prob': 0.0005215692217461765}, 
    {'label': 'Human Capital', 'prob': 0.0004274820093996823}, 
    {'label': 'Non-ESG', 'prob': 0.00039607062353752553}, 
    {'label': 'Business Ethics & Values', 'prob': 0.00028768458287231624}]]
```
### Named Entity Extraction
The ```EntityExtractor``` class is responsible for extracting entities from the given text. 

Model used - 'en_core_web_trf' from spacy library ( https://spacy.io/models/en )

English transformer pipeline (Transformer(name=‘roberta-base’, piece_encoder=‘byte-bpe’, stride=104, type=‘roberta’, width=768, window=144, vocab_size=50265)). 


__Evaluation metrics:(declared by spacy)__

- precision -   	0.90
- recall    -	    0.90
- F-score   -   	0.90

Use the following command to download spacy transformer model
```python

python -m spacy download en_core_web_trf

```



Currently, the class extracts 3 entities. 
- Organisation
- Person
- Geopolitical Entities

But,It can be extended to extract other entities available in this model. 
Below are the list of entities available in spacy transformer model.

- __CARDINAL__ : Numerals that do not fall under another type
- __DATE__: Absolute or relative dates or periods
- __EVENT__: Named hurricanes, battles, wars, sports events, etc.
- __FAC__: Buildings, airports, highways, bridges, etc.
- __GPE__: Countries, cities, states
- __LANGUAGE__: Any named language
- __LAW__: Named documents made into laws.
- __LOC__: Non-GPE locations, mountain ranges, bodies of water
- __MONEY__: Monetary values, including unit
- __NORP__: Nationalities or religious or political groups
- __ORDINAL__: "first", "second", etc.
- __ORG__: Companies, agencies, institutions, etc.
- __PERCENT__: Percentage, including "%"
- __PERSON__: People, including fictional
- __PRODUCT__: Objects, vehicles, foods, etc. (not services)
- __QUANTITY__: Measurements, as of weight or distance
- __TIME__: Times smaller than a day
- __WORK_OF_ART__: Titles of books, songs, etc.






Example usage of the class

```python
from named_entity_extraction import EntityExtractor

# Sample text
txt_1 = "Welcome to EcoScape Innovations, where sustainability meets innovation\
    in every aspect of our operations. Founded in 2010 by Emily Hayes, a passionate\
    environmentalist, EcoScape Innovations has been a pioneer in revolutionizing \
    how companies integrate eco-friendly practices into their business models.\
    Based in the heart of Portland, Oregon, our company was born out of a deep-rooted\
    commitment to preserving the planet for future generations. Emily Hayes, \
    a visionary entrepreneur, envisioned a world where businesses could thrive\
    while prioritizing environmental responsibility. With her unwavering determination,\
    she built EcoScape Innovations on the pillars of sustainability, innovation, and community."

ner_obj = EntityExtractor()
ner_obj.extract_entities(txt_1)

```
Output

```python

{
    'ORG': ['EcoScape Innovations'],
    'PERSON': ['Emily Hayes'],
    'GPE': ['Oregon', 'Portland']
    }


```

### Sentiment Analysis

The ```EsgSentimentAnalysis``` Class is responsible for providing a sentiment score for a given text.

Model used - 'TrajanovRisto/bert-esg' from Hugging Face (https://huggingface.co/TrajanovRisto/bert-esg)

Sentiment scores are between -1 and 1, where -1 indicates negative sentiment while 1 indicates positive sentiment.

### ESG Triplet/Relationship Extraction

The ```EsgTripletExtraction``` Class for extracting triplets in the following way:

Input: In accordance with our ambitious goal, the water withdrawal of the data center decreased remarkably from 3.874 million litres to 2.367 million litres across the past three years.

```python    
{"esg_category": "Water", 
"predicate": "Reduction of", 
"object": "The water withdrawal of the data center by 1.507 million litres"}
```    
It extracts categories of prepared using six distinct ESG data providers Sustainalytics, S&P Global, Refinitiv, Moody’s ESG, Morgan Stanley Capital International-MSCI, and MSCI-KLD. A predicate to this category and object of action taken with respect to the category. 
    
The prompt structure and model used are basically followed from this work: https://arxiv.org/pdf/2310.05628.pdf

Example usage of the class

```python

from corenlp.triplet_extraction import EsgTripletExtraction

# You can choose the model and input your huggingface key in case you are using a gated model in the constructor.
model_id = "TheBloke/wizardLM-7B-HF"
hf_auth = "Add your huggingface token here"
triplet_extractor = EsgTripletExtraction(model_id, hf_auth)
# Choose the list of stop words where model might stop hallicunating. 
stop_list = ['\nHuman:', '\n```\n']

triplet_extractor.make_extraction_chain(stop_list)

#choose either a single text to extract triplet
input_text = "In accordance with our ambitious goal, the water withdrawal of the data\
              center decreased remarkably from 3.874 million litres to 2.367 million litres across\
              the past three years."


output_one = triplet_extractor.extract_triplets(input_text)

#or list or iterable of texts to extract triplet
output_multi = triplet_extractor.extract_triplets([input_text, input_text])

```
The outputs would look like for single text.
```python
{'esg_category': 'Water', 
  'predicate': 'Reduction of', 
  'object': 'The water withdrawal of the data center by 1.507 million litres'}
```
Or a list for multi text entry.
```python
[{'esg_category': 'Water', 
'predicate': 'Reduction of', 
'object': 'The water withdrawal of the data center by 1.507 million litres'},
 {'esg_category': 'Water', 
 'predicate': 'Reduction of',
 'object': 'The water withdrawal of the data center by 1.507 million litres'}]
```
Evaluation of the framework was done by randomly choosing by 15 out of 300 examples generated by framework shown in [this notebook](https://dagshub.com/Omdena/Voy-Finance/src/main/src/tasks/NLP-tasks-exploration/esg-information-extraction/esg_ie.ipynb).
Accuracy for triplet element was:
- esg_category: 1.0
- predicate: 0.9333333333333333
- object: 1.0

### Controversy Detection Question Answering Based

Class for detecting controversies in source documents based on retrieval augmented generation (RAG). This procedure first retrieves text from the source documents based sentence transformer based embedding and then shows it to the llama based chatbot before asking it the final question. An example prompt is (from Langchain):

>Use the following pieces of context to answer the question at the end. If you don't know the answer, 
just say that you don't know, don't try to make up an answer.

>....retrieved content from documents....

>Question: Extract any contradictory or controversial statements about X company in the context text?
Helpful Answer:

For more information, please also have a look at [this notebook](https://dagshub.com/Omdena/Voy-Finance/src/main/src/tasks/NLP-tasks-exploration/controversy_detection_POC_llama7b/conterversy_detection.ipynb)

Example usage of the class

```python

from corenlp.controversy_detection import ControversyDetectionQABased

# You can choose the model and input your huggingface key in case you are using a gated model in the constructor.
model_id = "Weyaxi/OpenHermes-2.5-neural-chat-7b-v3-1-7B"
hf_auth = "Add your huggingface token here"
controversy_extractor = ControversyDetectionQABased(model_id, hf_auth)


# Choose a way how to feed documents to the extractors. Some examples are here:
# https://python.langchain.com/docs/modules/data_connection/document_loaders/
# An example of pandas based data frame is shown here.
import pandas as pd
from langchain.document_loaders import DataFrameLoader

documents = pd.read_csv("documents.csv")
content = DataFrameLoader(documents, "column_for_content").load()

# Choose the list of stop words where model might stop hallicunating. 
stop_list = ['\nHuman:', '\n```\n']

#make an extraction chain based on which embedding is needed to be used. 
embedding_model = "sentence-transformers/all-mpnet-base-v2"

controversy_extractor.make_extraction_chain(content, 
                                            stop_list,
                                            embedding_model)
                                            
#In case user needs to ask just the default question

controversy_extractor.show_default_answer()
```
> "The default question is: Extract any contradictory or controversial statements about X company in the context text?

>"Helpful Answer:
There doesn't seem to be any direct contradictory or controversial statements about X company in the given context.
However, the context discusses various risks and challenges faced by the company, such as legal proceedings, environmental issues, regulatory compliance, and potential human rights impacts. These aspects highlight both the complexity of the business environment and Linde's efforts to manage these risks responsibly.
For more information, please refer to documents with index
[14, 14, 10, 10]"

```python

#There could be follow up question or just start from 
#this question instead of asking default question first.
question = "Please extract three exact sentences from the context text which\ 
             mention potential risks and challenges that linde faces seperated\
             by next line. Please only extract exact sentences from context text\
             and do not modify the text"
             
controversy_extractor.question(question)

```
