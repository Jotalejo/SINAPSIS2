FROM python:slim-bullseye
RUN apt-get update && apt-get install -y default-libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requeriments.txt 
COPY . /app
CMD ["python", "app.py"]
