# Generate a Self-Signed SSL Certificate

```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout selfsigned.key \
  -out selfsigned.crt \
  -subj "/C=US/ST=Local/L=Local/O=Intranet/CN=CH_HOST"
```
