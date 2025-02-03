FROM alpine:3.18

# Install aria2 & curl for downloading the torrent file + selecting file
RUN apk add --no-cache aria2 curl

WORKDIR /app

# Copy our download script
COPY download.sh /app/download.sh
RUN chmod +x /app/download.sh

# Expose a directory for our final downloads
VOLUME ["/downloads"]

RUN apk add --no-cache bash
CMD ["/bin/bash", "/app/download.sh"]
