FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && apt-get clean

COPY printClusters.py /app/
# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "printClusters.py"]