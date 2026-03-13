#!/bin/sh
set -e

CERT_DIR="/etc/nginx/certs"
CERT_CRT="${CERT_DIR}/selfsigned.crt"
CERT_KEY="${CERT_DIR}/selfsigned.key"

if [ ! -f "$CERT_CRT" ] || [ ! -f "$CERT_KEY" ]; then
  mkdir -p "$CERT_DIR"
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$CERT_KEY" \
    -out "$CERT_CRT" \
    -subj "${CERT_SUBJ:-/C=US/ST=Local/L=Local/O=Intranet/CN=localhost}"
fi

if [ -f /etc/nginx/templates/default.conf.template ]; then
  : "${API_ORIGIN:=http://app:5000}"
  envsubst '$API_ORIGIN' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
fi

exec "$@"
