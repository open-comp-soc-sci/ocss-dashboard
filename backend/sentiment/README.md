# the process

the rpc client from the frontend is started when
the user of the website wants to conduct some analysis.

if the user wants to do some topic clustering then the rpc
client sends a queue to the topic_model_queue

the rpc client creates an ephemeral queue that is temporary and 
unnamed. once topic clustering is complete, the topic clustering
sends the results right back into that ephemeral queue. then the
rpc client can decide whether it wants to send those results to the
sentiment analysis.



# old

sentiment_analysis_consumer calls roberta.py.

roberta.py gets the data from readReddit which queries the backend.
