import os
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from collections import defaultdict

# Set your Hugging Face API token
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN', "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")
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

def run_nli_aspect_analysis(terms, sectioned_bodies, topics, batch_size=16):
    """
    For each (term, topic), batch all its example texts in one zero‑shot call.
    Returns a dict keyed by (term, topic) → {occurrences, positive/neutral/negative buckets}.
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

        # out is a list of { labels: [...], scores: [...] }
        for res in out:
            # pick top label
            lbl, scr = res["labels"][0], res["scores"][0]
            key = (term, topic)
            if key not in stats:
                stats[key] = {
                    "occurrences": 0,
                    "positive": {"count": 0, "avg_score": 0.0},
                    "neutral":  {"count": 0, "avg_score": 0.0},
                    "negative": {"count": 0, "avg_score": 0.0},
                }
            bucket = stats[key][lbl]
            stats[key]["occurrences"] += 1
            bucket["count"]     += 1
            bucket["avg_score"] += scr

    # finalize averages
    for v in stats.values():
        for sentiment in ("positive","neutral","negative"):
            cnt = v[sentiment]["count"]
            if cnt:
                v[sentiment]["avg_score"] /= cnt

    return stats
