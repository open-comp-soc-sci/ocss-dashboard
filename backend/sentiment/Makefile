REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null)
ENV_FILE ?= $(if $(REPO_ROOT),$(REPO_ROOT)/.env,.env)

ifneq ("$(wildcard $(ENV_FILE))","")
include $(ENV_FILE)
export
endif

run: down build
	docker run --name sentiment_container -d -v $(PWD):/app --env-file "$(ENV_FILE)" --gpus all sentiment
	make logs



build:
	docker build -t sentiment .  

rabbit: down
	docker run -d --name sentiment_container \
	--env-file "$(ENV_FILE)" \
	-p 5672:5672 -p 15672:15672 \
	sentiment


logs:
	docker logs -f sentiment_container

down:
	-docker stop sentiment_container
	-docker rm sentiment_container
