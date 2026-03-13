import pika
import socket
import os
import json
import threading
import time
import traceback
from app.redis_client import set_progress, get_progress, set_result, get_result


def _coerce_json(value):
    """Decode payloads that may already be dicts or JSON strings (possibly double-encoded)."""
    cur = value
    for _ in range(2):
        if isinstance(cur, str):
            try:
                cur = json.loads(cur)
            except Exception:
                break
        else:
            break
    return cur


def _queue_names(base: str, client_id: str):
    # Keep backward compatibility with workers that still publish to legacy queue names.
    return [f"{base}_{client_id}", base]


def create_connection():
    """Create and return a RabbitMQ connection."""
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_user = os.getenv('RABBITMQ_USER', 'user')
    rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')
    client_id = os.getenv('CLIENT_ID') or socket.gethostname()

    print(f"Connecting to RabbitMQ at {rabbitmq_host}:{rabbitmq_port} as {rabbitmq_user} (client {client_id})")

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

            client_id = os.getenv('CLIENT_ID') or socket.gethostname()
            progress_queues = _queue_names("progress_queue", client_id)
            for queue_name in progress_queues:
                channel.queue_declare(queue=queue_name, durable=True)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    job_id = data.get("job_id")

                    if job_id:
                        # Only set progress if result is not done yet
                        current = _coerce_json(get_progress(job_id))
                        current_stage = current.get("stage") if isinstance(current, dict) else None
                        if current_stage != "done":
                            set_progress(job_id, data)
                            print(f"Progress update for {job_id}")

                except Exception as e:
                    print("Error processing progress message:", e)
                    print(traceback.format_exc())

                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            for queue_name in progress_queues:
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=callback
                )

            print(f" [*] Listening for progress updates on queues: {progress_queues}")
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
            client_id = os.getenv('CLIENT_ID') or socket.gethostname()
            results_queues = _queue_names("results_queue", client_id)
            for queue_name in results_queues:
                channel.queue_declare(queue=queue_name, durable=True)

            def callback(ch, method, properties, body):
                try:
                    job_id = properties.correlation_id
                    if not job_id:
                        print("Received result without correlation_id")
                        return

                    result_data = json.loads(body)
                    set_result(job_id, result_data)
                    print(f"Result stored for job {job_id}")

                    # Mark progress as done
                    progress_data = {
                        "job_id": job_id,
                        "stage": "done",
                        "message": "done",
                        "percent": 1
                    }
                    set_progress(job_id, progress_data)
                    print(f"Progress marked done for job {job_id}")

                except Exception as e:
                    print("Error processing result message:", e)
                    print(traceback.format_exc())

                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            for queue_name in results_queues:
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=callback
                )

            print(f" [*] Listening for results on queues: {results_queues}")
            channel.start_consuming()

        except Exception as e:
            print("Results listener crashed:", e)
            print(traceback.format_exc())
            print("Retrying in 5 seconds...")
            time.sleep(5)


def run_progress_consumer(blocking=True):
    """Start both listeners. In blocking mode this process stays alive."""
    progress_thread = threading.Thread(
        target=start_progress_listener,
        daemon=not blocking
    )
    results_thread = threading.Thread(
        target=start_results_listener,
        daemon=not blocking
    )

    progress_thread.start()
    results_thread.start()
    print("Progress and results listeners started.")

    if blocking:
        progress_thread.join()
        results_thread.join()


if __name__ == "__main__":
    run_progress_consumer(blocking=True)
