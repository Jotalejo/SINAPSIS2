FROM python:3.12-slim-bullseye
RUN apt-get update && apt-get install -y pkg-config default-libmysqlclient-dev build-essential python3-dev && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt /app
RUN pip install --upgrade pip setuptools && pip install -r requirements.txt
COPY . /app
CMD ["python", "App.py"]
