hello: check-env down
	docker compose build
	docker compose up --detach
	make logs

local: check-env down
	docker compose build
	RUNNINGLOCAL=true docker compose up --detach --scale rabbitmq=0
	make logs

down:
	docker compose down

logs:
	docker compose logs -f


check-env:
	@if [ ! -f .env ]; then \
		echo ".env file not found. Please create one." >&2; \
		exit 1; \
	fi