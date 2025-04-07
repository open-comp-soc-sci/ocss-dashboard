# backend/robertamodel/Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install pika numpy

CMD ["python", "printClusters.py"]
