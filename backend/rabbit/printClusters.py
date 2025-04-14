import pika
import json
import numpy as np

class ClusterPrintingTest:
    def __init__(self):
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="sunshine.cise.ufl.edu", port=5672, 
                                                                       credentials=pika.PlainCredentials("user", "password")))
        channel = connection.channel()
        # Declare the same queue
        channel.queue_declare(queue="grouping_results", durable=True)
        channel.basic_consume(queue="grouping_results", on_message_callback=self.receive_groups)

        print(" [*] Waiting for messages. To exit, press CTRL+C")
        channel.start_consuming()

        connection.close()

    def receive_groups(self, ch, method, properties, body):
        self.groups =  np.array(json.loads(body))
        print("Received Data")
        print(body)

        # Simulate processing each cluster
        for group in range(1, self.groups.max() + 1):
            topics_group_i = np.where(self.groups == group)[0]

            print(f"Group #{group} contains the indicies {topics_group_i}")

        # Acknowledge message after processing
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # Only receive one message
        ch.stop_consuming()
        
if __name__ == '__main__':
    clusterPrinter = ClusterPrintingTest()