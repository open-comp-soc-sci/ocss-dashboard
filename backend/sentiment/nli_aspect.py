import os
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from statistics import median

# Set your Hugging Face API token
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN', "***REMOVED***")
os.environ['HUGGINGFACEHUB_API_TOKEN'] = HUGGINGFACE_API_TOKEN

# Detect GPU
device = 0 if torch.cuda.is_available() else -1  # 0 for first CUDA device, -1 for CPU

# zero‑shot model
_MODEL = "facebook/bart-large-mnli"
_tokenizer = AutoTokenizer.from_pretrained(_MODEL)
_model     = AutoModelForSequenceClassification.from_pretrained(_MODEL).to(
    "cuda" if device==0 else "cpu"
)
_nli = pipeline(
    "zero-shot-classification",
    model=_model,
    tokenizer=_tokenizer,
    device=device
)

def run_nli_aspect_analysis(
    terms,
    sectioned_bodies,
    topics,
    batch_size=16,
    max_examples_per_term=25
):
    """
    For each (term, topic), batch all its example texts in one zero‑shot call.
    Returns a dict keyed by (term, topic) with class buckets plus signed sentiment
    aggregates computed from the full label probability distribution for each text.
    """
    LABELS = ["positive","neutral","negative"]
    stats = {}

    for term, bodies, topic in zip(terms, sectioned_bodies, topics):
        if not bodies:
            continue

        # cap to avoid gigantic batches
        texts = [b[:512] for b in bodies[:1024]]

        # single hypothesis template per term
        hypothesis = f"This text expresses {{}} sentiment about '{term}'."
        out = _nli(
            texts,
            candidate_labels=LABELS,
            hypothesis_template=hypothesis,
            batch_size=batch_size
        )
        if isinstance(out, dict):
            out = [out]

        key = (term, topic)
        if key not in stats:
            stats[key] = {
                "occurrences": 0,
                "matched_count": len(bodies),
                "sampled_count": len(texts),
                "signed_sentiment_mean": 0.0,
                "signed_sentiment_median": 0.0,
                "positive": {"count": 0, "avg_score": 0.0},
                "neutral":  {"count": 0, "avg_score": 0.0},
                "negative": {"count": 0, "avg_score": 0.0},
                "examples": [],
                "_signed_scores": []
            }

        # out is a list of { labels: [...], scores: [...] }
        for text, res in zip(texts, out):
            label_scores = {
                label: float(score)
                for label, score in zip(res["labels"], res["scores"])
            }
            positive_score = label_scores.get("positive", 0.0)
            negative_score = label_scores.get("negative", 0.0)
            neutral_score = label_scores.get("neutral", 0.0)
            signed_score = positive_score - negative_score

            # pick top label
            lbl, scr = res["labels"][0], res["scores"][0]
            bucket = stats[key][lbl]
            stats[key]["occurrences"] += 1
            bucket["count"]     += 1
            bucket["avg_score"] += scr
            stats[key]["_signed_scores"].append(signed_score)

            if len(stats[key]["examples"]) < max_examples_per_term:
                stats[key]["examples"].append({
                    "label": lbl,
                    "score": float(scr),
                    "signed_score": signed_score,
                    "positive_score": positive_score,
                    "neutral_score": neutral_score,
                    "negative_score": negative_score,
                    "text": text
                })

    # finalize averages
    for v in stats.values():
        for sentiment in ("positive","neutral","negative"):
            cnt = v[sentiment]["count"]
            if cnt:
                v[sentiment]["avg_score"] /= cnt
        signed_scores = v.pop("_signed_scores", [])
        if signed_scores:
            v["signed_sentiment_mean"] = sum(signed_scores) / len(signed_scores)
            v["signed_sentiment_median"] = median(signed_scores)

    return stats
