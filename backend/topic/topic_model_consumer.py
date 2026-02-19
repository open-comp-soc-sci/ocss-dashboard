import json
import os
import pika
import copy
from topic_model_service import run_topic_model
from topic_model import config as base_config  # Import the complete configuration
import traceback

# Retrieve RabbitMQ connection details.
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
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
queue_name = 'topic_model_queue'
channel.queue_declare(queue=queue_name, durable=True)

def callback(ch, method, properties, body):
    print("Received message:", body)
    try:
        # Parse the JSON message.
        data = json.loads(body)
    except Exception as e:
        print("Error decoding JSON:", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Create a deep copy of the base configuration.
    config_copy = copy.deepcopy(base_config)

    # Update the configuration with any parameters provided in the message.
    if "job_id" in data:
        config_copy["job_id"] = data["job_id"]
    if "data_source" in data:
        config_copy["data_source"] = data["data_source"]
    if "subreddit" in data:
        config_copy["subreddit"] = data["subreddit"]
    if "option" in data:
        config_copy["option"] = data["option"]
    if "startDate" in data:
        config_copy["startDate"] = data["startDate"]
    if "endDate" in data:
        config_copy["endDate"] = data["endDate"]
    if "save_dir" in data:
        config_copy["save_dir"] = data["save_dir"]
    if "date" in data:
        config_copy["date"] = data["date"]

    # Use the save_dir from the config_copy as the output directory.
    output_dir = data.get("output_dir", config_copy["save_dir"])

    try:
        result_message = run_topic_model(config_copy["data_source"], output_dir, config_copy)
        # print("Topic modeling complete:", result_message)

        # Publish the reply to the callback queue specified in properties.reply_to
        response_body = json.dumps(result_message)
        ch.basic_publish(
            exchange='',
            routing_key='topic_results_queue', # send the data to the results queue
            properties=pika.BasicProperties(
                correlation_id=data["job_id"], # get the generated job id
                delivery_mode=2
            ),
            body=response_body
        )

    except Exception as e:
        print("Error running topic model:", e)
        print("Traceback:", traceback.format_exc())
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)



print(" [*] Waiting for messages. To exit press CTRL+C")
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()
