import pika
import json
import numpy as np

class ClusterPrintingTest:
    def __init__(self):
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq", port=5672))
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
            # Decode and load the cluster data
            cluster_data = np.array(json.loads(body))
            print("\nReceived Cluster Data:", cluster_data)

            # Process each cluster
            for group in range(1, cluster_data.max() + 1):
                topics_group_i = np.where(cluster_data == group)[0]
                print(f"Group #{group} contains the indices {topics_group_i}")

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    ClusterPrintingTest()
