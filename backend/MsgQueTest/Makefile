build:
	docker build -t msg_test .  

rabbit:
# Network can be ommitted once this has beed integrated into a docker-compose.yml file as compose automatically creates a network 
	docker network create mynetwork	
	docker run --network=mynetwork -d --name rabbitmq \
	-p 5672:5672 -p 15672:15672 \
	rabbitmq:management

run:
	docker run --network=mynetwork --name msg_test_container msg_test python3 printClusters.py

logs:
	docker logs -f msg_test_container

down:
	-docker stop msg_test
	-docker rm msg_test_container

rabbitdown:
	-docker stop rabbitmq
	-docker rm rabbitmq