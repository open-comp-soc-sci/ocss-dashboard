import os
import pika


def _rabbitmq_connection_parameters():
    """Build RabbitMQ connection params from environment settings."""
    if os.getenv("RUNNINGLOCAL") == "true":
        rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    else:
        rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")

    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user = os.getenv("RABBITMQ_USER", "user")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS", "password")
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)

    return pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials
    )

class TopicModelRpcClient:
    def __init__(self):
        self.connection_parameters = _rabbitmq_connection_parameters()
        print("Initializing TopicModelRpcClient...")

    def send_job(self, message: str, job_id: str):
        """
        Send a topic modeling job to RabbitMQ asynchronously.
        The frontend can track progress via /api/progress/<job_id>.
        """
        connection = pika.BlockingConnection(self.connection_parameters)
        try:
            channel = connection.channel()
            channel.basic_publish(
                exchange='',
                routing_key='topic_model_queue',
                properties=pika.BasicProperties(
                    correlation_id=job_id,
                    delivery_mode=2
                ),
                body=message
            )
        finally:
            connection.close()

        print(f"Sent topic modeling job {job_id} to topic_model_queue")

# RPC client to handle sentiment anylisis message passing
class SentimentAnalysisRpcClient:
    def __init__(self):
        self.connection_parameters = _rabbitmq_connection_parameters()
        print('Initializing SentimentAnalysisRpcClient...')

    def send_job(self, message: str, job_id: str):
        """Send job asynchronously; frontend tracks progress separately."""
        connection = pika.BlockingConnection(self.connection_parameters)
        try:
            channel = connection.channel()
            channel.basic_publish(
                exchange='',
                routing_key='sentiment_analysis_queue',
                properties=pika.BasicProperties(
                    correlation_id=job_id,
                    delivery_mode=2
                ),
                body=message
            )
        finally:
            connection.close()

        print(f"Sent sentiment analysis job {job_id} to sentiment_analysis_queue")
