import pika
import os
import json
import threading
import time
import traceback
from app.redis_client import set_progress, get_progress, set_result, get_result


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

            channel.queue_declare(queue="progress_queue", durable=True)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    job_id = data.get("job_id")

                    if job_id:
                        # Only set progress if result is not done yet
                        current = get_progress(job_id)
                        if not current or json.loads(current).get("stage") != "done":
                            set_progress(job_id, json.dumps(data))
                            print(f"Progress update for {job_id}")

                except Exception as e:
                    print("Error processing progress message:", e)
                    print(traceback.format_exc())

                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue="progress_queue",
                on_message_callback=callback
            )

            print(" [*] Listening for progress updates...")
            channel.start_consuming()

        except Exception as e:
            print("Progress listener crashed:", e)
            print(traceback.format_exc())
            print("Retrying in 5 seconds...")
            time.sleep(5)


def start_results_listener():
    """Listen for final results and store them in Redis."""
    while True:
        try:
            connection = create_connection()
            channel = connection.channel()
            channel.queue_declare(queue="results_queue", durable=True)

            def callback(ch, method, properties, body):
                try:
                    job_id = properties.correlation_id
                    if not job_id:
                        print("Received result without correlation_id")
                        return

                    result_data = json.loads(body)
                    set_result(job_id, json.dumps(result_data))
                    print(f"Result stored for job {job_id}")

                    # Mark progress as done
                    progress_data = {
                        "job_id": job_id,
                        "stage": "done",
                        "message": "done",
                        "percent": 1
                    }
                    set_progress(job_id, json.dumps(progress_data))
                    print(f"Progress marked done for job {job_id}")

                except Exception as e:
                    print("Error processing result message:", e)
                    print(traceback.format_exc())

                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue="results_queue",
                on_message_callback=callback
            )

            print(" [*] Listening for results...")
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
