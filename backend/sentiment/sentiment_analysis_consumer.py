import os
import json
import pika
import traceback
from readReddit import preproccess_termed_sentiment_data, load_dataframe
from nli_aspect import run_nli_aspect_analysis

# RabbitMQ setup
rabbitmq_host = os.getenv('RABBITMQ_HOST','sunshine.cise.ufl.edu')
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

def keywords_sentiment(df, topics):
    sentiment_stats = []

    for topic in topics:
        topic_num      = topic["topicNumber"]
        keywords_csv   = topic.get("ctfidfKeywords", "")
        if not keywords_csv:
            sentiment_stats.append({
                "topicNumber": topic_num,
                "error": "No keywords provided"
            })
            continue

        # grab only the first keyword
        first_kw = keywords_csv.split(",")[0].strip()

        # collect bodies that mention that first keyword
        bodies = [b for b in df["body"] if first_kw.lower() in b.lower()]
        bodies = list(dict.fromkeys(bodies))[:1000]

        print(f"[NLI] Topic {topic_num}: analyzing first keyword “{first_kw}”")
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
        meta     = grouping.get("meta",{})
        groups   = grouping.get("groups",[])
    except Exception as e:
        print("Invalid JSON:", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        df = load_dataframe(meta)
        # flatten out all topics
        all_topics = [t for g in groups for t in g.get("topics",[])]
        sentiment = keywords_sentiment(df, all_topics)

        reply = {"groups":groups, "sentiment":sentiment}
        channel.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=json.dumps(reply)
        )
        print("✅ NLI aspect analysis done.")
    except Exception as e:
        print("Error in consumer:", e)
        traceback.print_exc()
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

print(" [*] Waiting for messages on", queue_name)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()
