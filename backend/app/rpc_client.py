import pika
import uuid
import os
import json

class TopicModelRpcClient:
    def __init__(self):
        print("Initializing TopicModelRpcClient...")

        # Determine RabbitMQ host
        if os.getenv("RUNNINGLOCAL") == "true":
            rabbitmq_host = os.getenv("RABBITMQ_HOST", "sunshine.cise.ufl.edu")
        else:
            rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")

        rabbitmq_user = os.getenv("RABBITMQ_USER", "user")
        rabbitmq_pass = os.getenv("RABBITMQ_PASS", "password")

        # Create credentials and connection
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
        )
        self.channel = self.connection.channel()

        print("TopicModelRpcClient connected to RabbitMQ at", rabbitmq_host)

    def send_job(self, message: str, job_id: str):
        """
        Send a topic modeling job to RabbitMQ asynchronously.
        The frontend can track progress via /api/progress/<job_id>.
        """
        # Publish the message to the topic_model_queue
        self.channel.basic_publish(
            exchange='',
            routing_key='topic_model_queue',
            properties=pika.BasicProperties(
                correlation_id=job_id,  # job_id used as correlation_id
                delivery_mode=2  # persistent
            ),
            body=message
        )
        print(f"Sent topic modeling job {job_id} to topic_model_queue")

# RPC client to handle sentiment anylisis message passing
class SentimentAnalysisRpcClient:
    def __init__(self):
        print('Initializing SentimentAnalysisRpcClient...')

        # Determine RabbitMQ host
        if os.getenv("RUNNINGLOCAL") == "true":
            rabbitmq_host = os.getenv("RABBITMQ_HOST", "sunshine.cise.ufl.edu")
        else:
            rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")

        rabbitmq_user = os.getenv("RABBITMQ_USER", "user")
        rabbitmq_pass = os.getenv("RABBITMQ_PASS", "password")

        # Create credentials and connection
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
        )
        self.channel = self.connection.channel()


    def send_job(self, message: str, job_id: str):
        """Send job asynchronously; frontend tracks progress separately."""
        self.channel.basic_publish(
            exchange='',
            routing_key='sentiment_analysis_queue',
            properties=pika.BasicProperties(
                correlation_id=job_id,
                delivery_mode=2
            ),
            body=message
        )
        print(f"Sent sentiment analysis job {job_id} to sentiment_analysis_queue")