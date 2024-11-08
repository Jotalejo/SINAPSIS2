FROM python:slim-bullseye
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requeriments.txt 
COPY . /app
CMD ["python", "app.py"]
