import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from readpickle import filtered_bodies


# token is causing "secret" issues when pushing to github
# ill just message u guys the api token
HUGGINGFACE_API_TOKEN = '***REMOVED***'
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

# Iterate through each body text, classify sentiment, and print the result
for index, input_text in enumerate(filtered_bodies):
    if len(input_text) < 514:  # Only run for texts that are less than 514 characters
        result = run_classification(input_text)
        print(f"Index {index}: {input_text}")
        print(f"Classification: {result}\n")