# backend/topic/topic_model_consumer.py

import json
import os
import pika
from topic_model_service import run_topic_model

# Retrieve RabbitMQ connection details from environment variables or defaults.
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))

# Set up the RabbitMQ connection and channel.
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
)
channel = connection.channel()

# Declare (and ensure) the queue exists.
queue_name = 'topic_model_queue'
channel.queue_declare(queue=queue_name, durable=True)

# Default configuration for the topic model.
default_config = {
    'save_dir': '/app/saved',
    'data': '/app/full_db.pickle',
    'random_state': 42,
    # add other configuration parameters as needed...
}

def callback(ch, method, properties, body):
    print("Received message: ", body)
    try:
        # Expecting a JSON message with optional keys: data_source, output_dir
        data = json.loads(body)
    except Exception as e:
        print("Error decoding JSON: ", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    data_source = data.get("data_source", default_config['data'])
    output_dir = data.get("output_dir", default_config['save_dir'])

    try:
        result_message = run_topic_model(data_source, output_dir, default_config)
        print("Topic modeling complete: ", result_message)
    except Exception as e:
        print("Error running topic model: ", e)
    finally:
        # Acknowledge that the message has been processed.
        ch.basic_ack(delivery_tag=method.delivery_tag)

print(" [*] Waiting for messages. To exit press CTRL+C")
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()
