hello: down
	@if [ ! -f .env ]; then \
		echo ".env file not found. Please create one." >&2; \
		exit 1; \
	fi
	docker compose up --detach
	make logs


down:
	docker compose down

logs:
	docker compose logs -f

