FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Install basic dependencies and Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip gcc && \
    apt-get clean

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY printClusters.py /app/
COPY readReddit.py /app/
COPY nli_aspect.py /app/

CMD ["python3", "-u", "sentiment_analysis_consumer.py"]