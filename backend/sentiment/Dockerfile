FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && apt-get clean

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY printClusters.py /app/
COPY readReddit.py /app/
COPY roberta.py /app/

CMD ["python", "-u", "sentiment_analysis_consumer.py"]