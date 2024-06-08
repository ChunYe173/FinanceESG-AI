# This is a sample code for Named Entity Recognition (NER) using spaCy.

import spacy
import random
from spacy.training.example import Example


def ner_analysis():
    # Example data
    train_data = [
        ("Apple is a technology company.", {"entities": [(0, 5, "ORG")]}),
        ("Microsoft develops Windows.", {"entities": [(0, 9, "ORG")]}),
    ]

    # Load spaCy English model
    nlp = spacy.load("en_core_web_sm")

    # Train the NER model on the initial data
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")

    # Add labels to the NER pipe
    for _, annotations in train_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # Disable other pipes during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        # Training loop
        for epoch in range(10):  # Adjust the number of epochs as needed
            random.shuffle(train_data)
            losses = {}
            examples = []
            for text, annotations in train_data:
                example = Example.from_dict(nlp.make_doc(text), annotations)
                examples.append(example)

            # Update the model with examples
            nlp.update(examples, drop=0.5, losses=losses)

    # Save the trained model
    nlp.to_disk("ner_model")

    # Load the trained model
    loaded_nlp = spacy.load("ner_model")

    # Example of using the trained model on new data
    # new_text = "Tesla employees went on vacation with Air Canada."
    new_text = "Apple Inc. was founded by Steve Jobs in Cupertino"
    doc = loaded_nlp(new_text)

    results = {}
    # Print the entities in the new text
    for ent in doc.ents:
        print(ent.text, ent.label_)
        results[ent.text] = ent.label_
    return results
