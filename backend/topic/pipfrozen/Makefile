IP_ADDRESS := $(shell docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ollama_container)

.PHONY: download first stop down logs build run

# First-time setup
first: stop
	@if [ ! -f posts.jsonl ] || [ ! -f comments.jsonl ]; then \
		$(MAKE) download; \
	fi
	$(MAKE) build
	$(MAKE) run
	$(MAKE) logs

# Build Docker Image
build:
	
	docker build -t topicmodelfrozen .

run:
	docker run -d \
	--network=mynetwork \
	--gpus all \
	--name topicmodelfrozen_container \
	-v ~/.cache/huggingface:/root/.cache/huggingface \
	-v ${CURDIR}:/app \
	-e OLLAMA_IP_ADDRESS=$(IP_ADDRESS) \
	topicmodelfrozen python3 topic_model.py /app/full_db.pickle /app/output/




# Download Reddit Data only if missing
download:
	@test -f posts.jsonl || wget -O posts.jsonl \
	"https://uflorida-my.sharepoint.com/:u:/g/personal/j_fleischer_ufl_edu/EYEgNU-F4EROnYltlg7GqOABU6zfOd1wFA-42n2aso3KqQ?download=1"
	
	@test -f comments.jsonl || wget -O comments.jsonl \
	"https://uflorida-my.sharepoint.com/:u:/g/personal/j_fleischer_ufl_edu/Ec5tYgVXqC9LmB-ciuP7e0EBIwRxhhplcvNujQ1jxJMJ9Q?download=1"

# Stop the container
stop:
	-docker stop topicmodelfrozen_container && docker rm topicmodelfrozen_container

# Stop and remove all associated data
down: stop
	-docker rmi topicmodelfrozen

# View logs
logs:
	docker logs -f topicmodelfrozen_container

shell:
	docker exec -it topicmodelfrozen_container /bin/bash