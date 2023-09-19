FROM python:3.11-alpine
LABEL authors="apaes"

RUN apk add docker

WORKDIR /dnr/
COPY requirements.txt main.py event.py host.py /dnr/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
