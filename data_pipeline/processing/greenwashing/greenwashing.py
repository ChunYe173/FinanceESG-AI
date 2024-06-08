"""
Collection of functions related to producing Greenwashing insights
"""
import torch

def run_inference_on_text(tokenizer, model, input_texts:list[str]):
    tokenized_data = tokenizer(input_texts, truncation=True, padding=True, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**tokenized_data)
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1)
    return probabilities[:, 1].tolist()
