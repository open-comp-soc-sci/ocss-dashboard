import pika
import os
import json
import numpy as np
import sys
import subprocess

class ClusterPrintingTest:
    def __init__(self):
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="sunshine.cise.ufl.edu", port=5672, 
                                                                       credentials=pika.PlainCredentials("user", "password")))
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
            if not body or body.strip() == b'':
                print("Received an empty message.")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            print(f"\nRaw message body: {body!r}")

            decoded_str = body.decode('utf-8')
            print(f"Decoded string: {decoded_str[:500]}...")  # Print first 500 chars only if it's big
            sys.stdout.flush()

            decoded_json = json.loads(decoded_str)
            print("Successfully parsed JSON.")
            sys.stdout.flush()


            with open("grouping_results.json", "w") as f:
                print(f"Wrote to: {os.path.abspath('grouping_results.json')}")
                sys.stdout.flush()
                print("Writing to file...")
                sys.stdout.flush()
                json.dump(decoded_json, f, indent=2)
                print("Done writing.")
                sys.stdout.flush()

            print("Running readReddit.py...")
            sys.stdout.flush()

            subprocess.run(["python", "readReddit.py"], check=True)

            print("Finished running readReddit.py")
            sys.stdout.flush()

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            print(f"Other error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


if __name__ == '__main__':
    ClusterPrintingTest()