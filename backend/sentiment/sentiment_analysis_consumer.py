import json
import os
import pika
import copy
from roberta import run_roberta_analysis, run_topic_roberta_analysis
from readReddit import preproccess_termed_sentiment_data, load_dataframe
import traceback

# Retrieve RabbitMQ connection details.
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'sunshine.cise.ufl.edu')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
rabbitmq_user = os.getenv('RABBITMQ_USER', 'user')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')

print("Connecting to RabbitMQ at", rabbitmq_host, "with user", rabbitmq_user)

# Set up the credentials and connection.
credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials, heartbeat=65530)
)
channel = connection.channel()

# Declare (and ensure) the queue exists.
queue_name = 'sentiment_analysis_queue'
channel.queue_declare(queue=queue_name, durable=True)

# Determines whether sentiment analysis is done by term or by topic
termed = True

def keywords_sentiment(df, topics, all_sectioned_bodies):
    sentiment_stats = []

    for topic in topics:
        topicNumber = topic.get("topicNumber")
        ctfidfKeywords = topic.get("ctfidfKeywords", "")
        topicLabel = topic.get("topicLabel")
        if not ctfidfKeywords:
            sentiment_stats.append({"topicNumber": topicNumber, "error": "No text provided"})
            continue

        keywords_strip = [keyword.strip() for keyword in ctfidfKeywords.split(",")]

        per_keyword_bodies = []
        for keyword in keywords_strip:
            matched_bodies = [
                body for body in df["body"] if keyword.lower() in body.lower()
            ]
            unique_bodies = list(set(matched_bodies))[:1000]
            per_keyword_bodies.append(unique_bodies)
            # print(f"Keyword: {keyword} — Matched {len(unique_bodies)} unique bodies")

        try:
            print(f"[Sentiment] Running sentiment on Topic {topicNumber}: {topicLabel}. Analyzing keywords: {ctfidfKeywords}")
            keywords_stats = run_roberta_analysis(
                keywords_strip,
                per_keyword_bodies,
                [topicNumber] * len(keywords_strip)
            )

            topic_stats = {t["topicNumber"]: [] for t in topics}
            for term in keywords_strip:
                topic_stats[topicNumber].append({
                    "keyword": term,
                    "sentiment": keywords_stats.get((term, topicNumber), {})
                })

            sentiment_stats.append({
                "topicNumber": topicNumber,
                "ctfidfKeywords": ctfidfKeywords,
                "sentiment": topic_stats.get(topicNumber, [])
            })
            print("Test Sentiment Finish")

        except Exception as e:
            sentiment_stats.append({"topicNumber": topicNumber, "error": str(e)})

    return sentiment_stats

def callback(ch, method, properties, body):
    try:
        # 1) Parse the full topic‑clustering payload
        grouping_data = json.loads(body)
        meta   = grouping_data.get("meta")
        groups = grouping_data.get("groups", [])
    except Exception as e:
        print("Error decoding JSON:", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        # 2) Load your DataFrame from the meta info
        df = load_dataframe(meta)

        # 3) Build a flat list of all topic dicts
        if termed:
            # Prepare bodies by topic if you need them
            all_sectioned_bodies = preproccess_termed_sentiment_data(df, groups)
            # Now pull out every topic from every group
            all_topics = []
            for group in groups:
                all_topics.extend(group.get("topics", []))
            # 4) Run your per‑keyword sentiment
            sentiment_stats = keywords_sentiment(df, all_topics, all_sectioned_bodies)

        else:
            # If you decided to do topic‑level sentiment instead
            all_topics = [t for g in groups for t in g.get("topics", [])]
            sentiment_stats = run_topic_roberta_analysis(df, all_topics)

        print("Sentiment Analysis complete:", sentiment_stats)

        # 5) Reply with the original groups + your new sentiment array
        result_message = {
            "groups":    groups,
            "sentiment": sentiment_stats
        }
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=json.dumps(result_message)
        )

    except Exception as e:
        print("Error running sentiment analysis:", e)
        print(traceback.format_exc())

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

print(" [*] Waiting for Sentiment Analysis message. To exit press CTRL+C")
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()






