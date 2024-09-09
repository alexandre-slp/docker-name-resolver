FROM python:3.11-alpine AS build
LABEL authors="apaes"

RUN apk add binutils

ENV WORKDIR="/dnr"

WORKDIR ${WORKDIR}

COPY requirements.txt main.py event.py host.py ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pyinstaller --onefile --clean --noconfirm --name=dnr main.py

FROM build AS release
LABEL authors="apaes"

RUN apk add docker

WORKDIR ${WORKDIR}

COPY --from=build ${WORKDIR}/dist/dnr ./

RUN touch hosts

ENTRYPOINT ["./dnr"]
