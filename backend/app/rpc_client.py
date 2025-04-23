import pika
import uuid
import os
import json

class TopicModelRpcClient:
    def __init__(self):
        # Retrieve RabbitMQ connection details from environment variables.
        print('heres Topic Model rpc client!')
        print('RUNNINGLOCAL', os.getenv('RUNNINGLOCAL'))
        if os.getenv('RUNNINGLOCAL') == 'true':
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'sunshine.cise.ufl.edu')
        else:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        rabbitmq_user = os.getenv('RABBITMQ_USER', 'user')
        rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')
        
        # Create credentials object.
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host,
                credentials=credentials
            )
        )
        self.channel = self.connection.channel()
        # Set auto_delete=True so that the exclusive queue is removed after use.
        result = self.channel.queue_declare(queue='', exclusive=True, auto_delete=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self, ch, method, properties, body):
        # Check that the response corresponds to the request we made.
        if self.corr_id == properties.correlation_id:
            self.response = body

    def call(self, message):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        # Note the change to routing_key 'topic_model_queue' (matching the consumer)
        self.channel.basic_publish(
            exchange='',
            routing_key='topic_model_queue',  # must match the consumer's queue
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                delivery_mode=2  # persistent message
            ),
            body=message
        )
        # Wait until we receive a response (consider adding a timeout in production)
        while self.response is None:
            self.connection.process_data_events()
        return self.response.decode('utf-8')

# RPC client to handle sentiment anylisis message passing
class SentimentAnalysisRpcClient:
    def __init__(self):
        # Retrieve RabbitMQ connection details from environment variables.
        print('heres sentiment rpc client')
        print('RUNNINGLOCAL', os.getenv('RUNNINGLOCAL'))
        if os.getenv('RUNNINGLOCAL') == 'true':
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'sunshine.cise.ufl.edu')
        else:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        rabbitmq_user = os.getenv('RABBITMQ_USER', 'user')
        rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')
        
        # Create credentials object.
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host,
                credentials=credentials
            )
        )
        self.channel = self.connection.channel()
        # Set auto_delete=True so that the exclusive queue is removed after use.
        result = self.channel.queue_declare(queue='', exclusive=True, auto_delete=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self, ch, method, properties, body):
        # Check that the response corresponds to the request we made.
        if self.corr_id == properties.correlation_id:
            self.response = body

    def call(self, message):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        # Note the change to routing_key 'topic_model_queue' (matching the consumer)
        self.channel.basic_publish(
            exchange='',
            routing_key='sentiment_analysis_queue',  # must match the consumer's queue
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                delivery_mode=2  # persistent message
            ),
            body=message
        )
        # Wait until we receive a response (consider adding a timeout in production)
        while self.response is None:
            self.connection.process_data_events()
        return self.response.decode('utf-8')