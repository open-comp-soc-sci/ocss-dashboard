IP_ADDRESS := $(shell docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ollama_container)

.PHONY: first stop down logs build run

# First-time setup
first: stop
	$(MAKE) build
	$(MAKE) run
	$(MAKE) logs

# Build Docker Image
build:
	
	docker build -t topic_model_api .

run:
	docker run -d \
	--network=mynetwork \
	--gpus all \
	--name topic_model_consumer_container \
	-v ~/.cache/huggingface:/root/.cache/huggingface \
	-v ${CURDIR}:/app \
	-e OLLAMA_IP_ADDRESS=$(IP_ADDRESS) \
	-e RABBITMQ_HOST=rabbitmq \
	 topic_model_api




# Download Reddit Data only if missing
download:
	@test -f posts.jsonl || wget -O posts.jsonl \
	"https://uflorida-my.sharepoint.com/:u:/g/personal/j_fleischer_ufl_edu/EYEgNU-F4EROnYltlg7GqOABU6zfOd1wFA-42n2aso3KqQ?download=1"
	
	@test -f comments.jsonl || wget -O comments.jsonl \
	"https://uflorida-my.sharepoint.com/:u:/g/personal/j_fleischer_ufl_edu/Ec5tYgVXqC9LmB-ciuP7e0EBIwRxhhplcvNujQ1jxJMJ9Q?download=1"

# Stop the container
stop:
	-docker stop topic_model_api_container && docker rm topic_model_api_container

# Stop and remove all associated data
down: stop
	-docker rmi topic_model_api

# View logs
logs:
	docker logs -f topic_model_api_container

shell:
	docker exec -it topic_model_api_container /bin/bash