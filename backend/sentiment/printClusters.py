import pika
import os
import json
import sys
import readReddit  # Import the module directly

class SentimentClusterConsuming:
    def __init__(self):
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="sunshine.cise.ufl.edu",
                port=5672, 
                credentials=pika.PlainCredentials("user", "password")
            )
        )
        channel = connection.channel()

        # Declare the same queue
        channel.queue_declare(queue="grouping_results", durable=True)

        # Set up the callback for receiving messages
        channel.basic_consume(queue="grouping_results", on_message_callback=self.receive_groups)

        print(" [*] Waiting for cluster messages. To exit, press CTRL+C", flush=True)
        channel.start_consuming()

        connection.close()

    def receive_groups(self, ch, method, properties, body):
        try:
            if not body or body.strip() == b'':
                print("Received an empty message.", flush=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            print(f"\nRaw message body: {body!r}", flush=True)

            decoded_str = body.decode('utf-8')
            print(f"Decoded string: {decoded_str[:500]}...", flush=True)  # Print first 500 chars only if it's big

            decoded_json = json.loads(decoded_str)
            print("Successfully parsed JSON.", flush=True)

            # Save the message to file for developer convenience or later processing
            with open("grouping_results.json", "w") as f:
                print(f"Wrote to: {os.path.abspath('grouping_results.json')}", flush=True)
                print("Writing to file...", flush=True)
                json.dump(decoded_json, f, indent=2)
                print("Done writing.", flush=True)

            print("Running readReddit.main()...", flush=True)
            readReddit.main()  # Directly call the main function from readReddit

            print("Finished running readReddit.main()", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            print(f"Other error: {e}", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

if __name__ == '__main__':
    SentimentClusterConsuming()
