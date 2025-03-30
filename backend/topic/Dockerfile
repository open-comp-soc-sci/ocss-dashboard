# Dockerfile for Topic Modeling Consumer

FROM python:3.11-slim

WORKDIR /app

# Install gcc and other dependencies
RUN apt-get update && apt-get install -y gcc && apt-get clean

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files into the container.
COPY . /app/

# (Optional) Expose a port if you need to debug or monitor via a separate endpoint.
EXPOSE 5001

# Set the default command to run the consumer
CMD ["python3", "-u", "topic_model_consumer.py"]
