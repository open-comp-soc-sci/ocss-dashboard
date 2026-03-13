import os
import json
import pika
import re
import traceback
from readReddit import preproccess_termed_sentiment_data, load_dataframe
from nli_aspect import run_nli_aspect_analysis

# RabbitMQ setup
rabbitmq_host = os.getenv('RABBITMQ_HOST','rabbitmq')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT','5672'))
rabbitmq_user = os.getenv('RABBITMQ_USER','user')
rabbitmq_pass = os.getenv('RABBITMQ_PASS','password')

credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials,
        heartbeat=65530
    )
)
channel = connection.channel()
queue_name = 'sentiment_analysis_queue'
channel.queue_declare(queue=queue_name, durable=True)


def publish_progress(job_id, stage, message, percent, client_id=None):
    client_id = client_id or os.getenv("CLIENT_ID") or __import__("socket").gethostname()
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials
        )
    )
    channel = connection.channel()
    progress_queue = f"progress_queue_{client_id}"
    channel.queue_declare(queue=progress_queue, durable=True)

    progress_message = {
        "job_id": job_id,
        "stage": stage,
        "message": message,
        "percent": percent
    }

    channel.basic_publish(
        exchange="",
        routing_key=progress_queue,
        body=json.dumps(progress_message),
        properties=pika.BasicProperties(delivery_mode=2)
    )

    connection.close()


def publish_results(job_id, reply, client_id=None):
    client_id = client_id or os.getenv("CLIENT_ID") or __import__("socket").gethostname()
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials
        )
    )
    channel = connection.channel()
    results_queue = f"results_queue_{client_id}"
    channel.queue_declare(queue=results_queue, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=results_queue,
        body=json.dumps(reply),
        properties=pika.BasicProperties(
            delivery_mode=2,
            correlation_id=job_id
        )
    )
    connection.close()


def _normalize_keyword_set(custom_keywords):
    if isinstance(custom_keywords, str):
        custom_keywords = [custom_keywords]

    normalized = []
    seen = set()
    for kw in custom_keywords or []:
        if not isinstance(kw, str):
            continue
        trimmed = kw.strip()
        if not trimmed:
            continue
        lowered = trimmed.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(trimmed)
    return normalized


def _keyword_in_body(keyword, body):
    if not isinstance(keyword, str) or not keyword.strip() or not isinstance(body, str):
        return False
    pattern = re.compile(rf"(?<!\w){re.escape(keyword.strip())}(?!\w)", re.IGNORECASE)
    return bool(pattern.search(body))


def keywords_sentiment(df, topics, job_id, custom_keywords=None, client_id=None):
    sentiment_stats = []

    seen_keywords = set()
    total_topics = len(topics)
    normalized_custom = _normalize_keyword_set(custom_keywords)

    if normalized_custom:
        total_custom = len(normalized_custom)
        for idx, first_kw in enumerate(normalized_custom):
            topic_num = idx + 1
            bodies = [b for b in df["body"] if _keyword_in_body(first_kw, b)]
            bodies = list(dict.fromkeys(bodies))[:1000]

            progress_percent = ((idx + 1) / total_custom) if total_custom else 1
            publish_progress(
                job_id=job_id,
                stage="analyzing_keyword",
                message=f"Keyword {idx+1}/{total_custom}: analyzing '{first_kw}'",
                percent=progress_percent,
                client_id=client_id
            )

            if not bodies:
                sentiment_stats.append({
                    "topicNumber": topic_num,
                    "ctfidfKeywords": "",
                    "error": "No matching posts/comments found for this custom keyword",
                    "sentiment": [
                        {
                            "keyword": first_kw,
                            "sentiment": {
                                "negative": {"count": 0, "avg_score": 0},
                                "neutral": {"count": 0, "avg_score": 0},
                                "positive": {"count": 0, "avg_score": 0}
                            }
                        }
                    ]
                })
                continue

            print(f"[NLI] Custom keyword {idx+1}/{total_custom}: "
                  f"\u201c{first_kw}\u201d")
            stats = run_nli_aspect_analysis(
                terms=[first_kw],
                sectioned_bodies=[bodies],
                topics=[topic_num]
            )

            sentiment_stats.append({
                "topicNumber": topic_num,
                "ctfidfKeywords": "",
                "sentiment": [
                    {
                        "keyword": first_kw,
                        "sentiment": stats.get((first_kw, topic_num), {})
                    }
                ]
            })

        return sentiment_stats

    for idx, topic in enumerate(topics):
        topic_num      = topic["topicNumber"]
        keywords_csv   = topic.get("ctfidfKeywords", "")
        if not keywords_csv:
            sentiment_stats.append({
                "topicNumber": topic_num,
                "error": "No keywords provided"
            })
            continue

        topic_keywords = [kw.strip() for kw in keywords_csv.split(",") if kw.strip()]
        # Default behavior: analyze the first c-TF-IDF keyword.
        first_kw = topic_keywords[0]

        if first_kw.lower() in seen_keywords:
            # keyword already processed, skip it.
            continue
        seen_keywords.add(first_kw.lower())

        # collect bodies that mention that first keyword
        bodies = [b for b in df["body"] if _keyword_in_body(first_kw, b)]
        bodies = list(dict.fromkeys(bodies))[:1000]

        # Publish progress
        progress_percent = ((idx + 1) / total_topics) if total_topics else 1
        publish_progress(
            job_id=job_id,
            stage="analyzing_keyword",
            message=f"Topic {idx+1}/{total_topics}: analyzing keyword '{first_kw}'",
            percent=progress_percent,
            client_id=client_id
        )

        print(f"[NLI] Topic {topic_num}: analyzing first keyword "
              f"\u201c{first_kw}\u201d")
        stats = run_nli_aspect_analysis(
            terms=[first_kw],
            sectioned_bodies=[bodies],
            topics=[topic_num]
        )

        # pack back into your output shape
        sentiment_stats.append({
            "topicNumber":   topic_num,
            "ctfidfKeywords": keywords_csv,
            "sentiment": [
              {
                "keyword": first_kw,
                "sentiment": stats.get((first_kw, topic_num), {})
              }
            ]
        })

    return sentiment_stats


def callback(ch, method, properties, body):
    try:
        grouping = json.loads(body)
        if isinstance(grouping, dict) and isinstance(grouping.get("topic_result"), dict):
            # Backward/forward compatibility: allow wrapper payload shape.
            custom_keywords = grouping.get("custom_keywords", [])
            grouping = grouping["topic_result"]
        else:
            custom_keywords = grouping.get("custom_keywords", []) if isinstance(grouping, dict) else []

        meta     = grouping.get("meta",{})
        groups   = grouping.get("groups",[])
        job_id   = grouping["job_id"]
    except Exception as e:
        print("Invalid JSON:", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    client_id = (grouping.get("client_id") if isinstance(grouping, dict) else None) or os.getenv("CLIENT_ID") or __import__("socket").gethostname()
    publish_progress(job_id, "started", "Starting sentiment analysis", 0.0, client_id=client_id)

    try:
        df = load_dataframe(meta)
        # flatten out all topics
        all_topics = [t for g in groups for t in g.get("topics",[])]
        sentiment = keywords_sentiment(
            df,
            all_topics,
            job_id,
            custom_keywords=custom_keywords,
            client_id=client_id
        )

        # publish results
        reply = {"groups":groups, "sentiment":sentiment}
        publish_results(job_id, reply, client_id=client_id)
        print(f"[RESULTS] Published results for job {job_id}")
        publish_progress(job_id, "done", "done", 1.0, client_id=client_id)

        print("✅ NLI aspect analysis done.")
    except Exception as e:
        print("Error in consumer:", e)
        publish_progress(job_id, "error", "Error during sentiment analysis", 0.0)
        traceback.print_exc()
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

print(" [*] Waiting for messages on", queue_name)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()
