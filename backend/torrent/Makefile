# Makefile

IMAGE_NAME = clickhouse/clickhouse-server:latest
CONTAINER_NAME = clickhouse_server_auto

# Directory containing JSONL files to ingest (if you want to mount them)
LOCAL_DIR = ~/ocss/reddit/comments
CONTAINER_DIR = /data/jsonl

# Directory on your host to store ClickHouse data
# so the database persists across container restarts
LOCAL_DB_DIR = ~/ocss/reddit/db_data
CONTAINER_DB_DIR = /var/lib/clickhouse

.PHONY: run stop logs

## Run the official ClickHouse container with persistent storage
run: stop
	docker run -d --name $(CONTAINER_NAME) \
		-p 9000:9000 \
		-p 8123:8123 \
		-e CLICKHOUSE_USER=default \
		-e CLICKHOUSE_PASSWORD=heyheyhey \
		-v $(LOCAL_DB_DIR):$(CONTAINER_DB_DIR) \
		-v $(LOCAL_DIR):$(CONTAINER_DIR) \
		$(IMAGE_NAME)

## Stop and remove the container if it exists
stop down:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

## View container logs
logs:
	docker logs -f $(CONTAINER_NAME)

## Exec into the container with a bash shell
bash:
	docker exec -it $(CONTAINER_NAME) bash

send:
	nohup python -u insert_data.py ~/ocss/reddit/comments/RC_2024-01 | tee output.log &



drop:
	docker exec -it $(CONTAINER_NAME) \
		clickhouse-client \
		--user=default \
		--password=heyheyhey \
		--query="DROP TABLE IF EXISTS reddit_comments"

# inside:
# docker exec -it $(CONTAINER_NAME) /bin/bash
#clickhouse-client --user=default --password=heyheyhey
