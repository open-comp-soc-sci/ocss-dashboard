REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null)
ENV_FILE ?= $(if $(REPO_ROOT),$(REPO_ROOT)/.env,.env)

ifneq ("$(wildcard $(ENV_FILE))","")
include $(ENV_FILE)
export
endif

OLLAMA_HOST ?= ollama_container
CH_HOST ?= localhost
RABBITMQ_HOST ?= $(CH_HOST)

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
	-docker network create ocss
	-docker network connect ocss $(OLLAMA_HOST)
	docker run -d \
	--gpus all \
	--name topic_model_api_container \
	--network ocss \
	-v ~/.cache/huggingface:/root/.cache/huggingface \
	-v ${CURDIR}:/app \
	--env-file "$(ENV_FILE)" \
	-e OLLAMA_IP_ADDRESS=http://$(OLLAMA_HOST):11434 \
	-e RABBITMQ_HOST="$(RABBITMQ_HOST)" \
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
