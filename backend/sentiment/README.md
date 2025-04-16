# gpt generated

RabbitMQ Message Arrival for Clusters:

    An external process (or service) sends a RabbitMQ message into the grouping_results queue.

Cluster Message Handling in sentiment_consumer.py:

    The sentiment_consumer.py program (started by the Dockerfile) is running as a RabbitMQ consumer.

    It waits for messages on the grouping_results queue.

    When a message arrives, its callback (receive_groups) is triggered:

        It prints the raw and decoded message.

        It writes the JSON content to a file named grouping_results.json.

        It then triggers further processing by calling readReddit.py via a subprocess.

Data Fetching and Sentiment Analysis in readReddit.py:

    readReddit.py starts as a subprocess called by sentiment_consumer.py.

    It loads grouping_results.json to extract metadata (meta) and grouping information (groups).

    Using values from meta, it builds an external API URL and fetches additional data (e.g., Reddit posts) via an HTTP GET request.

    The fetched data is converted into a Pandas DataFrame.

    It then pre-processes the data by grouping text according to provided keywords using the function preproccess_sentiment_data.

    For each group, it calls run_roberta_analysis (from the roberta.py module) to perform sentiment analysis on the text.

    The computed sentiment statistics are printed out for logging and/or debugging purposes.

(Optional) Sentiment Analysis via RPC:

    Separately, a different consumer, sentiment_analysis_consumer.py, listens on the sentiment_analysis_queue.

    When a message is sent to this queue:

        sentiment_analysis_consumer.py receives the message.

        It extracts the necessary metadata and grouping data.

        It follows a similar process as in readReddit.py to fetch data, pre-process it, and perform sentiment analysis.

        Finally, it sends the analysis results back using RabbitMQ’s RPC reply mechanism (publishing the result to the callback queue specified in the message).

    This RPC mechanism allows another component (or service) to receive the sentiment analysis result asynchronously.

# old

sentiment_analysis_consumer calls roberta.py.

roberta.py gets the data from readReddit which queries the backend.
