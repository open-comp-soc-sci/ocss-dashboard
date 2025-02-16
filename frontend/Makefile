run: stop build
	docker run --name frontend_container -d -p 8001:8001 -v ${CURDIR}:/app frontend sh -c "npm install && npx vite --host 0.0.0.0 --port 8001"


build:
	docker build -t frontend .


stop down:
	-docker stop frontend_container 
	-docker rm frontend_container
