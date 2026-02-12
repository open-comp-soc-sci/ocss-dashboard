import pika
import os
import json
import threading

# In-memory progress storage
progress_store = {}
result_store = {}

def start_progress_listener():
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    rabbitmq_user = os.getenv('RABBITMQ_USER', 'user')
    rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            credentials=credentials
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue="topic_progress_queue", durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        job_id = data.get("jobId")

        if job_id:
            progress_store[job_id] = data
            print("Progress update:", data)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue="topic_progress_queue",
        on_message_callback=callback
    )

    print(" [*] Listening for topic progress updates...")
    channel.start_consuming()


def start_results_listener():
    connection = pika.BlockingConnection(...)
    channel = connection.channel()
    channel.queue_declare(queue="topic_results_queue", durable=True)

    def callback(ch, method, properties, body):
        job_id = properties.correlation_id
        result_store[job_id] = json.loads(body)

        # mark progress as done
        progress_store[job_id] = {
            "job_id": job_id,
            "stage": "done",
            "percent": 1
        }

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue="topic_results_queue",
        on_message_callback=callback
    )

    channel.start_consuming()


def run_progress_consumer():
    progress_thread = threading.Thread(
        target=start_progress_listener,
        daemon=True
    )

    results_thread = threading.Thread(
        target=start_results_listener,
        daemon=True
    )

    progress_thread.start()
    results_thread.start()
