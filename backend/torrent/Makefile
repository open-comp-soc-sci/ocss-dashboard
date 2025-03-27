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
		-p 9003:9000 \
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
	# nohup python -u insert_data.py ~/ocss/reddit/comments/RC_2024-01 | tee output.log &
	# nohup python -u insert_data.py ~/ocss/reddit/comments/RC_2024-02 | tee output.log &
	# nohup python -u insert_data.py ~/ocss/reddit/comments/RC_2024-03 | tee output.log &

	# python manager.py ~/ocss/reddit/comments/RC_2024-03 16
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-04 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-05.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-06.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-07.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-08.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-09.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-10.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-11.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/comments/RC_2024-12.zst 16 | tee manager_output.log &

	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-01.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-02.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-03.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-04.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-05.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-06.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-07.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-08.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-09.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-10.zst 16 | tee manager_output.log &
	# nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-11.zst 16 | tee manager_output.log &
	nohup python -u manager.py ~/ocss/reddit/submissions/RS_2024-12.zst 16 | tee manager_output.log &



drop:
	docker exec -it $(CONTAINER_NAME) \
		clickhouse-client \
		--user=default \
		--password=heyheyhey \
		--query="DROP TABLE IF EXISTS reddit_comments"

selective-drop:
	docker exec -it $(CONTAINER_NAME) \
		clickhouse-client \
		--user=default \
		--password=heyheyhey \
		--query="ALTER TABLE reddit_comments DELETE WHERE file_name LIKE 'RC_2024-12%';"


# inside:
# docker exec -it $(CONTAINER_NAME) /bin/bash
#clickhouse-client --user=default --password=heyheyhey
