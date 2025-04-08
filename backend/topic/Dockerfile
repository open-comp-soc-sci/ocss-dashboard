FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04


# Install basic dependencies and Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip gcc && \
    apt-get clean

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt


RUN pip install \
    --extra-index-url=https://pypi.nvidia.com \
    "cudf-cu12==25.2.*" "dask-cudf-cu12==25.2.*" "cuml-cu12==25.2.*" \
    "cugraph-cu12==25.2.*" "nx-cugraph-cu12==25.2.*" "cuspatial-cu12==25.2.*" \
    "cuproj-cu12==25.2.*" "cuxfilter-cu12==25.2.*" "cucim-cu12==25.2.*" \
    "pylibraft-cu12==25.2.*" "raft-dask-cu12==25.2.*" "cuvs-cu12==25.2.*" \
    "nx-cugraph-cu12==25.2.*"



# Copy all files into the container.
COPY . /app/

# (Optional) Expose a port if needed.
EXPOSE 5001

CMD ["python3", "-u", "topic_model_consumer.py"]
