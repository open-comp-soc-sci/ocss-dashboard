testing:
	docker build -t torrent-downloader .
	docker run --rm -v "${CURDIR}/downloads:/downloads" torrent-downloader



hi: stop
	docker build -t torrent-downloader .
	docker run --rm \
	  -e MAGNET_LINK="magnet:?xt=urn:btih:56aa49f9653ba545f48df2e33679f014d2829c10" \
  		-e SELECT_FILE=2 \
  		-v "${CURDIR}/downloads:/app/downloads" \
	torrent-downloader

stop down:
	@CONTAINERS=$$(docker ps -q -f ancestor=torrent-downloader)
	-docker stop $$CONTAINERS
	-docker rm $$CONTAINERS
