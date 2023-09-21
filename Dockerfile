FROM python:3.11-alpine
LABEL authors="apaes"

RUN apk add docker

WORKDIR /dnr/
COPY requirements.txt main.py event.py host.py /dnr/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
CMD ["python", "main.py", "--help"]
