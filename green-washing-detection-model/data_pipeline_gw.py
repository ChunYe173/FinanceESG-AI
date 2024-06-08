##Greenwashing claim
## Model on https://huggingface.co/tushar27/Env-Claims
## API key (read) "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"

#Dependecies
# pip install transformers
# pip install torch
# pip install pandas
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd

def load_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return tokenizer, model

def preprocess_data(data_path, tokenizer):
    df = pd.read_csv(data_path)  # Replace with the path to Insights dataset
    sentences = df['text_column'].tolist()  # Replace 'text_column' with the actual column name containing text data
    tokenized_data = tokenizer(sentences, truncation=True, padding=True, return_tensors='pt')
    return tokenized_data

def classify_text(tokenized_data, model):
    with torch.no_grad():
        outputs = model(**tokenized_data)
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1)
    return probabilities[:, 1].tolist()  # binary classification; adjust accordingly

def main():
    model_name = "tushar27/Env-Claims"  # Hugging Face model name
    tokenizer, model = load_model(model_name)

    data_path = "path/to/your/dataset.csv"  # Replace with the path to dataset
    tokenized_data = preprocess_data(data_path, tokenizer)

    predictions = classify_text(tokenized_data, model)

    # Assuming  a 'label' column in dataset 
    df['predicted_probability'] = predictions
    df.to_csv("path/to/output/predictions.csv", index=False)

if __name__ == "__main__":
    main()
