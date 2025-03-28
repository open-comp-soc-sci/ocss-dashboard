import pika
import uuid
import os
import json

class TopicModelRpcClient:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST', 'rabbitmq'))
        )
        self.channel = self.connection.channel()
        # Declare an exclusive callback queue for responses.
        result = self.channel.queue_declare(queue='', exclusive=True)
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
        self.channel.basic_publish(
            exchange='',
            routing_key='sentiment_analysis_queue',  # the queue your consumer listens on
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
