import os
import numpy as np
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from datasets import Dataset
from collections import defaultdict

# Set your Hugging Face API token
HUGGINGFACE_API_TOKEN = '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'
os.environ['HUGGINGFACEHUB_API_TOKEN'] = HUGGINGFACE_API_TOKEN

print("AAAAAA", flush=True)
model_name = "cardiffnlp/twitter-roberta-base-sentiment"

# Detect GPU
device = 0 if torch.cuda.is_available() else -1  # 0 for first CUDA device, -1 for CPU
print(f"Using device: {'cuda:0' if device == 0 else 'cpu'}")

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Move model to GPU (and half precision if available)
if device == 0:
    model = model.to("cuda").half()

# Create pipeline with device
classifier = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
    device=device
)
print("BBBBBBBB", flush=True)

def run_roberta_analysis(terms, sectioned_bodies, topics, batch_size: int = 32):
    """
    Runs sentiment analysis using a HuggingFace Dataset for efficient GPU batching.
    Args:
        terms: list of strings
        sectioned_bodies: list of lists of texts (one list per term)
        batch_size: number of texts per GPU batch
    Returns:
        term_stats: dict with sentiment statistics per term
    """

    term_topic_stats = {}
    topic_to_terms = defaultdict(list)

    for term, bodies, topic in zip(terms, sectioned_bodies, topics):
        # print(f"Term: {term}, Matched Bodies: {len(bodies)}")
        if not bodies:
            continue

        key = (term, topic)
        if key not in term_topic_stats:
            term_topic_stats[key] = {
                "occurrences": 0,
                "positive": {"count": 0, "avg_score": 0.0},
                "negative": {"count": 0, "avg_score": 0.0},
                "neutral": {"count": 0, "avg_score": 0.0},
            }
        topic_to_terms[topic].append(term)

        # Prepare the texts, truncated to fit the max length of the model
        texts = [body[:512] for body in bodies[:1000]]
        
        # Skip empty texts
        if not texts:
            print(f"[SKIP] Term: {term} — No valid texts to analyze.")
            continue

        # Build a dataset
        ds = Dataset.from_dict({"text": texts})

        # print(f"Term: {term} — Body text: {bodies[:3]}")
        # print(f"Term: {term} — Text count: {len(texts)}")
        # Define inference function
        def infer(batch):
            results = classifier(
                batch["text"],
                truncation=True,
                max_length=512,
                batch_size=batch_size
            )
            # print(f"Infer {len(results)} results")
            return {
                "label": [r["label"] for r in results],
                "score": [r["score"] for r in results]
            }

        ds = ds.map(infer, batched=True, batch_size=batch_size)

        # Aggregate stats
        for label, score in zip(ds["label"], ds["score"]):
            term_topic_stats[key]["occurrences"] += 1        
            if label == 'LABEL_2':
                bucket = term_topic_stats[key]["positive"]
            elif label == 'LABEL_0':
                bucket = term_topic_stats[key]["negative"]
            else:
                bucket = term_topic_stats[key]["neutral"]           
            bucket["count"] += 1
            bucket["avg_score"] += score

    # Final averaging of the sentiment scores
    for stats in term_topic_stats.values():
        for sentiment in ["positive", "negative", "neutral"]:
            cnt = stats[sentiment]["count"]
            if cnt > 0:
                stats[sentiment]["avg_score"] /= cnt

    return term_topic_stats


def run_topic_roberta_analysis(df, allTopics, batch_size: int = 32):
    """
    Runs topic-level sentiment averaging via HuggingFace Dataset mapping.
    """
    topics_array = np.array(allTopics)
    topic_stats = []

    for topic in range(topics_array.max() + 1):
        inds = np.where(topics_array == topic)[0]
        texts = [df['body'][i][:512] for i in inds]
        # print("Texts Topics: ", texts)
        ds = Dataset.from_dict({"text": texts})

        def infer(batch):
            results = classifier(
                batch["text"],
                truncation=True,
                max_length=512,
                batch_size=batch_size
            )
            return {
                "label": [r["label"] for r in results],
                "score": [r["score"] for r in results]
            }

        ds = ds.map(infer, batched=True, batch_size=batch_size)

        # Compute average score
        total_score = 0
        for label, score in zip(ds["label"], ds["score"]):
            if label == 'LABEL_2':
                total_score += score
            elif label == 'LABEL_0':
                total_score -= score
        avg_score = total_score / len(texts) if texts else 0
        topic_stats.append({"topic": topic, "score": avg_score})

    return topic_stats