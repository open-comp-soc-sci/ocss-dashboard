import os
import numpy as np
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from datasets import Dataset

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


def run_roberta_analysis(terms, sectioned_bodies, batch_size: int = 32):
    """
    Runs sentiment analysis using a HuggingFace Dataset for efficient GPU batching.
    Args:
        terms: list of strings
        sectioned_bodies: list of lists of texts (one list per term)
        batch_size: number of texts per GPU batch
    Returns:
        term_stats: dict with sentiment statistics per term
    """
    term_stats = {
        term: {
            "occurrences": 0,
            "positive": {"count": 0, "avg_score": 0},
            "negative": {"count": 0, "avg_score": 0},
            "neutral": {"count": 0, "avg_score": 0},
        }
        for term in terms
    }

    for term, bodies in zip(terms, sectioned_bodies):
        texts = [body[:512] for body in bodies[:1000] if len(body) < 1024]
        # Build a Dataset
        ds = Dataset.from_dict({"text": texts})

        # Define inference function
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

        # Run batched map
        ds = ds.map(infer, batched=True, batch_size=batch_size)

        # Aggregate stats
        for label, score in zip(ds["label"], ds["score"]):
            term_stats[term]["occurrences"] += 1
            if label == 'LABEL_2':
                ts = term_stats[term]["positive"]
            elif label == 'LABEL_0':
                ts = term_stats[term]["negative"]
            else:
                ts = term_stats[term]["neutral"]
            ts["count"] += 1
            ts["avg_score"] += score

    # Final averaging
    for stats in term_stats.values():
        for sentiment in ["positive", "negative", "neutral"]:
            cnt = stats[sentiment]["count"]
            if cnt > 0:
                stats[sentiment]["avg_score"] /= cnt

    # Print summary
    most_occ = max(term_stats, key=lambda t: term_stats[t]["occurrences"])
    least_occ = min(term_stats, key=lambda t: term_stats[t]["occurrences"])
    print(f"Most occurred term: {most_occ} ({term_stats[most_occ]['occurrences']})")
    print(f"Least occurred term: {least_occ} ({term_stats[least_occ]['occurrences']})")
    for term, stats in term_stats.items():
        print(f"{term}: Occurrences: {stats['occurrences']}, "
              f"Positive: {stats['positive']['count']} (Avg: {stats['positive']['avg_score']:.2f}), "
              f"Negative: {stats['negative']['count']} (Avg: {stats['negative']['avg_score']:.2f}), "
              f"Neutral: {stats['neutral']['count']} (Avg: {stats['neutral']['avg_score']:.2f})")

    return term_stats


def run_topic_roberta_analysis(df, allTopics, batch_size: int = 32):
    """
    Runs topic-level sentiment averaging via HuggingFace Dataset mapping.
    """
    topics_array = np.array(allTopics)
    topic_stats = []

    for topic in range(topics_array.max() + 1):
        inds = np.where(topics_array == topic)[0]
        texts = [df['body'][i][:512] for i in inds]
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
