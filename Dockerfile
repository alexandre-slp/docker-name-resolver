ENV WORKDIR="/dnr"

FROM python:3.11-alpine as base
LABEL authors="apaes"

WORKDIR ${WORKDIR}

COPY requirements.txt main.py event.py host.py ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pyinstaller --onefile --clean --noconfirm --name=dnr main.py

FROM base as release
LABEL authors="apaes"

RUN apk add docker

WORKDIR ${WORKDIR}

COPY --from=base ${WORKDIR}/dist/dnr ./

RUN touch hosts

ENTRYPOINT ["./dnr"]
