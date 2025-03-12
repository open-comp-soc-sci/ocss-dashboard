FROM python:3.11-slim

WORKDIR /app

# Install gcc
RUN apt-get update && apt-get install -y gcc && apt-get clean

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the topic modeling script
COPY topic_model.py /app/
COPY full_db.pickle /app/

# Set the default command
CMD ["python3", "topic_model.py"]