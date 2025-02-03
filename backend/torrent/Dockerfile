# Use a lightweight Python image
FROM python:3.9-slim-buster

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . /app

# Ensure the downloads directory exists
RUN mkdir -p /app/downloads

# Expose ports for torrents
EXPOSE 6881 6891

# Run the torrent download script
CMD ["python3", "download_torrent.py"]
