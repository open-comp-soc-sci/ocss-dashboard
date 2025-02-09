import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Set Up Your HuggingFace API Token
HUGGINGFACE_API_TOKEN = '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'
os.environ['HUGGINGFACEHUB_API_TOKEN'] = HUGGINGFACE_API_TOKEN

# Loading a Pre-Trained Model from HuggingFace Hub
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

# Creating a Function to Run the Application
def run_classification(text):
    result = classifier(text)
    return result

# Running the Application
input_text = "I love using HuggingFace models for NLP tasks!"
result = run_classification(input_text)
print(f"Input: {input_text}")
print(f"Classification: {result}")
