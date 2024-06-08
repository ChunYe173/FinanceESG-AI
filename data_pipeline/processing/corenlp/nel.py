import spacy
from spacy.kb import InMemoryLookupKB, KnowledgeBase
import csv
from pathlib import Path

class CustomNEL:

    
    def __init__(self, nlp_path, ner_custom_path = None):
        #nlp_path contains the English trained pipeline with a custom entity linking component
        self.nlp = spacy.load(nlp_path)
        #kb_path is custom knowledge base
        # self.kb_path = kb_path
        #initializing knowledge base
        self.kb = KnowledgeBase(vocab=self.nlp.vocab, entity_vector_length=300)
        #retrieving local knowledge base
        # self.kb.from_disk(kb_path)

    def predict(self, texts):
        docs = self.nlp.pipe(texts)
        text_label_id_list = []
        for doc in docs:
            text_label_id_list.append([(ent.text, ent.label_, ent.kb_id_) for ent in doc.ents])
        return text_label_id_list

#     import spacy
#     from spacy.kb import Entity
#
#     # Load existing NEL model
#     nlp = spacy.load('existing_model')
#
#     # Process new documents
#     for doc in new_docs:
#
#       doc = nlp(doc.text)
#
#       # Add entities to knowledge base
#       for ent in doc.ents:
#         nlp.kb.add_entity(KnowledgeBase(ent.text, ent.label_))
#
#     # Update model
#     nlp.to_disk('updated_model')
#
# entity = KnowledgeBase.create_entity(text, label)
# nlp.kb.add_entity(entity)
