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
termed = False

def callback(ch, method, properties, body):
    print("Received message:", body)
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
            
            sentiment_stats = []
            for terms, sectioned_bodies in all_sectioned_bodies:
                term_stats = run_roberta_analysis(terms, sectioned_bodies)
                sentiment_stats.append(term_stats)
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