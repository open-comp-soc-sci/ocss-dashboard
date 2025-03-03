run: check stop build
	docker run --name frontend_container \
	-d -p 8001:8001 \
	-v ${CURDIR}:/app \
	--env-file .env \
	frontend sh -c "npm install && npx vite --host 0.0.0.0 --port 8001"


build:
	docker build -t frontend .

stop down:
	-docker stop frontend_container 
	-docker rm frontend_container

check:
	@if [ ! -f .env ]; then \
		echo ".env file does not exist. Please create it before running make and review the readme on how to set up the .env"; \
		exit 1; \
	fi