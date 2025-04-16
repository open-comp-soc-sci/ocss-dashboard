run: down build
	docker run --name sentiment_container -d -v $(PWD):/app sentiment
	make logs



build:
	docker build -t sentiment .  

rabbit: down
	docker run -d --name sentiment_container \
	-p 5672:5672 -p 15672:15672 \
	sentiment


logs:
	docker logs -f sentiment_container

down:
	-docker stop sentiment_container
	-docker rm sentiment_container
