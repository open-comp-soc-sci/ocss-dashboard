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
    # print("Received message:", body)
    try:
        # Parse the JSON message.
        grouping_data = json.loads(body)
        meta = grouping_data["meta"]
        groups = grouping_data["groups"]
    except Exception as e:
        print("Error decoding JSON:", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        df = load_dataframe(meta)
        if termed:
            all_sectioned_bodies = preproccess_termed_sentiment_data(df, groups)
            #print("All sectioned bodies: ", all_sectioned_bodies)
            if "groups" in grouping_data:
                all_topics = []

            for group in grouping_data["groups"]:
                all_topics.extend(group.get("topics", []))
            sentiment_stats = keywords_sentiment(df, all_topics, all_sectioned_bodies)
        else:
            sentiment_stats = run_topic_roberta_analysis(df, grouping_data["allTopics"])
            
  
        print("Sentiment Analysis complete:", sentiment_stats)

        result_message = {
            "groups": groups,
            "sentiment": sentiment_stats
        }
        # Publish the reply to the callback queue specified in properties.reply_to
        response_body = json.dumps(result_message)
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,  # send reply to the callback queue
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=response_body
        )
    except Exception as e:
        print("Error running topic model:", e)
        print("Traceback:", traceback.format_exc())
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

print(" [*] Waiting for Sentiment Analysis message. To exit press CTRL+C")
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()





















