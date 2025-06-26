CONTAINER_NAME := ocss-backend

make:
	-docker stop ${CONTAINER_NAME}
	-docker rm ${CONTAINER_NAME}
	docker build -t ${CONTAINER_NAME} .
	MSYS_NO_PATHCONV=1 docker run --name ${CONTAINER_NAME} -d \
		-v "${CURDIR}:/app" \
		--env-file ../.env \
		-w /app \
	${CONTAINER_NAME}
	# docker logs --follow `docker ps -aqf ancestor=${CONTAINER_NAME} | head -n 1`

logs log:
	docker logs --follow `docker ps -aqf ancestor=${CONTAINER_NAME} | head -n 1`

down:
	@CONTAINERS=$$(docker ps -q -f ancestor=${CONTAINER_NAME}); \
	if [ -n "$$CONTAINERS" ]; then \
		for container in $$CONTAINERS; do \
			echo "Stopping container: $$container"; \
			docker stop $$container; \
			echo "Removing container: $$container"; \
			docker rm $$container; \
		done; \
	else \
		echo "No containers to stop or remove."; \
	fi
	# docker stop `docker ps -aqf ancestor=${CONTAINER_NAME} | head -n 1`
	# docker rm `docker ps -aqf ancestor=${CONTAINER_NAME} | head -n 1`

