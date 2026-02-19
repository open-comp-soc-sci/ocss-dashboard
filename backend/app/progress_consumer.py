import pika
import os
import json
import threading
import time
import traceback

# In-memory progress storage
progress_store = {}
result_store = {}


def create_connection():
    """Create and return a RabbitMQ connection."""
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_user = os.getenv('RABBITMQ_USER', 'user')
    rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')

    print(f"Connecting to RabbitMQ at {rabbitmq_host}:{rabbitmq_port} as {rabbitmq_user}")

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)

    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials,
            heartbeat=600
        )
    )


def start_progress_listener():
    """Listen for progress updates."""
    while True:
        try:
            connection = create_connection()
            channel = connection.channel()

            channel.queue_declare(queue="topic_progress_queue", durable=True)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    job_id = data.get("job_id")

                    if job_id:
                        progress_store[job_id] = data
                        print("Progress update:", data)

                except Exception as e:
                    print("Error processing progress message:", e)
                    print(traceback.format_exc())

                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue="topic_progress_queue",
                on_message_callback=callback
            )

            print(" [*] Listening for topic progress updates...")
            channel.start_consuming()

        except Exception as e:
            print("Progress listener crashed:", e)
            print(traceback.format_exc())
            print("Retrying in 5 seconds...")
            time.sleep(5)


def start_results_listener():
    """Listen for final topic modeling results."""
    while True:
        try:
            connection = create_connection()
            channel = connection.channel()

            channel.queue_declare(queue="topic_results_queue", durable=True)

            def callback(ch, method, properties, body):
                try:
                    job_id = properties.correlation_id
                    result_store[job_id] = json.loads(body)

                    # Mark progress as done
                    progress_store[job_id] = {
                        "job_id": job_id,
                        "stage": "done",
                        "percent": 1
                    }

                    print(f"Result received for job {job_id}")

                except Exception as e:
                    print("Error processing result message:", e)
                    print(traceback.format_exc())

                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue="topic_results_queue",
                on_message_callback=callback
            )

            print(" [*] Listening for topic results...")
            channel.start_consuming()

        except Exception as e:
            print("Results listener crashed:", e)
            print(traceback.format_exc())
            print("Retrying in 5 seconds...")
            time.sleep(5)


def run_progress_consumer():
    """Start both listeners in background daemon threads."""

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

    print("Progress and results listeners started.")
