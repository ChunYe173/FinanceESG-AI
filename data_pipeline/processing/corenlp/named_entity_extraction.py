import spacy

class EntityExtractor:
  def __init__(self):
    # load NER transformer model from spacy
    self.nlp = spacy.load('en_core_web_trf')
    
  def extract_entities(self, text: str) -> dict[str, list]:
    """
    This module takes in text and returns a dictionary of entities
    Parameters:
    -----------
    text: str
      input text
    Returns:
    --------
    Dictionary with entity type as key and list of entities as values
    
    Eg:
    {
      'ORG': ['EcoScape Innovations'],
      'PERSON': ['Emily Hayes'],
      'GPE': ['Portland', 'Oregon'] }

    """

    # initialize a dictionary with required entities   
    entities = {"ORG":[], "PERSON":[], "GPE":[]}
    doc = self.nlp(text)
    # loop through the identified entities and append detected entities to the dictionary
    for entity in doc.ents:
        if entity.label_ == 'ORG' and entity.text.lower():
            entities["ORG"].append(entity.text)
        if entity.label_ == 'PERSON' and entity.text.lower():
            entities["PERSON"].append(entity.text)
        if entity.label_ == 'GPE' and entity.text.lower():
            entities["GPE"].append(entity.text)

    processed_entities = self.post_process(entities)

    return processed_entities

  @staticmethod
  def post_process(ent_dict) -> dict[str, list]: 
      """
      This module postprocess the extracted entities.
      - Remove duplicates
      - Remove unwanted organisation names(other than company names)

      """
      # if organization is identified more than once it will appear multiple times in list
      # used set() to remove duplicates then convert back to list
      ent_dict["ORG"] = list(set(ent_dict["ORG"] ))
      ent_dict["PERSON"] = list(set(ent_dict["PERSON"] ))
      ent_dict["GPE"] = list(set(ent_dict["GPE"] ))

      # Created a list of organizations detected by the model which is not the name of a company
      # Used frequently occuring words from a financial text dataset to create this list
      # Can be modified as needed for our dataset
      non_org_list = ['tsx','eur', 'company','cse', 'nyse', 'tsx-v', 'tsx-v:','the “corporation', 'corporation',
            'eps','group','board of directors', 'the board of directors', 'the tSX venture exchange',
            'fda', 'board']
      
      org_list =  [org for org in ent_dict["ORG"] if org not in non_org_list]
      ent_dict["ORG"] = org_list
      return ent_dict
    
      
      

