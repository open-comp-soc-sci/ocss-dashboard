FROM python:3.9-slim-buster
WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

EXPOSE 5000

CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port", "5000"]