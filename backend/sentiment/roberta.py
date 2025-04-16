import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

HUGGINGFACE_API_TOKEN = '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'
os.environ['HUGGINGFACEHUB_API_TOKEN'] = HUGGINGFACE_API_TOKEN

# Loading a Pre-Trained Model from HuggingFace Hub
# Fine-tuned for sentiment analysis on Twitter data (subject to change)
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)


def run_roberta_analysis(terms, sectioned_bodies):
    # # LABEL_2 : Positive
    # # LABEL_1 : NEUTRAL
    # # LABEL_0 : Negativec

    def run_classification(text):
        result = classifier(text)[0]  # Extract first result
        return {"label": result['label'], "score": result['score']}

    # For each term:
    # Counts the amount of times a term occurs
    # Counts the amount of time each sentiment occurs
    # Calculates the average confidence score for each sentiment
    term_stats = {
        term: {
            "occurrences": 0,
            "positive": {"count": 0, "avg_score": 0},
            "negative": {"count": 0, "avg_score": 0},
            "neutral": {"count": 0, "avg_score": 0}
        } 
        for term in terms
    }

    for term, bodies in zip(terms, sectioned_bodies):
        for body in bodies[:1000]:
            if len(body) < 514:
                result = run_classification(body)
                label = result['label']
                score = result['score']

                # Term occurence count
                term_stats[term]["occurrences"] += 1

                # Categorize sentiment and update counts/scores
                if label == 'LABEL_2':  # Positive
                    term_stats[term]["positive"]["count"] += 1
                    term_stats[term]["positive"]["avg_score"] += score
                elif label == 'LABEL_0':  # Negative
                    term_stats[term]["negative"]["count"] += 1
                    term_stats[term]["negative"]["avg_score"] += score
                else:  # Neutral (LABEL_1)
                    term_stats[term]["neutral"]["count"] += 1
                    term_stats[term]["neutral"]["avg_score"] += score

    # Calculate average sentiment scores
    for term, stats in term_stats.items():
        if stats["positive"]["count"] > 0:
            stats["positive"]["avg_score"] /= stats["positive"]["count"]
        if stats["negative"]["count"] > 0:
            stats["negative"]["avg_score"] /= stats["negative"]["count"]
        if stats["neutral"]["count"] > 0:
            stats["neutral"]["avg_score"] /= stats["neutral"]["count"]

    # Identifies:
    # Which term occurred the most
    # Which term ocurred the least
    # Which terms on average are the most positively/negatively occurring
    # Which terms on average are the least positively/negatively occurring
    most_occurred = max(term_stats, key=lambda x: term_stats[x]["occurrences"])
    least_occurred = min(term_stats, key=lambda x: term_stats[x]["occurrences"])
    most_positive = max(term_stats, key=lambda x: term_stats[x]["positive"]["count"] / term_stats[x]["occurrences"] if term_stats[x]["occurrences"] > 0 else 0)
    least_positive = min(term_stats, key=lambda x: term_stats[x]["positive"]["count"] / term_stats[x]["occurrences"] if term_stats[x]["occurrences"] > 0 else 0)
    most_negative = max(term_stats, key=lambda x: term_stats[x]["negative"]["count"] / term_stats[x]["occurrences"] if term_stats[x]["occurrences"] > 0 else 0)
    least_negative = min(term_stats, key=lambda x: term_stats[x]["negative"]["count"] / term_stats[x]["occurrences"] if term_stats[x]["occurrences"] > 0 else 0)

    # Prints the average sentiment confidence scores
    for term, stats in term_stats.items():
        print(f"{term}: Occurrences: {stats['occurrences']}, "
            f"Positive: {stats['positive']['count']} (Avg Score: {stats['positive']['avg_score']:.2f}), "
            f"Negative: {stats['negative']['count']} (Avg Score: {stats['negative']['avg_score']:.2f}), "
            f"Neutral: {stats['neutral']['count']} (Avg Score: {stats['neutral']['avg_score']:.2f})")

    # Prints occurrence stats
    print(f"Most occurred term: {most_occurred} ({term_stats[most_occurred]['occurrences']})")
    print(f"Least occurred term: {least_occurred} ({term_stats[least_occurred]['occurrences']})")
    print(f"Most positively occurring term: {most_positive} ({term_stats[most_positive]['positive']['count'] / term_stats[most_positive]['occurrences']:.2f})")
    print(f"Least positively occurring term: {least_positive} ({term_stats[least_positive]['positive']['count'] / term_stats[least_positive]['occurrences']:.2f})")
    print(f"Most negatively occurring term: {most_negative} ({term_stats[most_negative]['negative']['count'] / term_stats[most_negative]['occurrences']:.2f})")
    print(f"Least negatively occurring term: {least_negative} ({term_stats[least_negative]['negative']['count'] / term_stats[least_negative]['occurrences']:.2f})")

    return term_stats
