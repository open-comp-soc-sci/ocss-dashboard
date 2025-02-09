import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification


# token is causing "secret" issues when pushing to github
# ill just message u guys the api token
HUGGINGFACE_API_TOKEN = ' '
os.environ['HUGGINGFACEHUB_API_TOKEN'] = HUGGINGFACE_API_TOKEN


# Loading a Pre-Trained Model from HuggingFace Hub
# Fine-tuned for sentiment analysis on Twitter data (subject to change)
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)


classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)


def run_classification(text):
   result = classifier(text)
   return result


# LABEL_2 : Positive
# LABEL_1 : NEUTRAL
# LABEL_0 : Negative


input_text = "I love using HuggingFace models for NLP tasks!"
result = run_classification(input_text)
print(f"Input: {input_text}")
print(f"Classification: {result}")
