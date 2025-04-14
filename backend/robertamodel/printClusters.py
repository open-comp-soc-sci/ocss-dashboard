import pika
import json
import numpy as np

class ClusterPrintingTest:
    def __init__(self):
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost", port=5672))
        channel = connection.channel()

        # Declare the same queue
        channel.queue_declare(queue="grouping_results", durable=True)

        # Set up the callback for receiving messages
        channel.basic_consume(queue="grouping_results", on_message_callback=self.receive_groups)

        print(" [*] Waiting for cluster messages. To exit, press CTRL+C")
        channel.start_consuming()

        connection.close()

    def receive_groups(self, ch, method, properties, body):
        try:
            # Decode and load the cluster JSON message
            decoded_json = json.loads(body)
            print("\nReceived Cluster Data JSON")

            # Save JSON to file for reuse
            with open("grouping_results.json", "w") as f:
                json.dump(decoded_json, f, indent=2)

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    ClusterPrintingTest()
