FROM python:3.11-slim
WORKDIR /app/MsgQueTest
COPY printClusters.py .
RUN pip install pika
CMD ["python", "printClusters.py"]