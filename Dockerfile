FROM python:3.11-alpine AS build
LABEL authors="apaes"

RUN apk add binutils

ENV WORKDIR="/dnr"

WORKDIR ${WORKDIR}

COPY requirements.txt main.py event.py network.py nginx.py status_template.html ${WORKDIR}

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pyinstaller --onefile --clean --noconfirm --name=dnr main.py

FROM nginx:alpine AS release
LABEL authors="apaes"

ENV WORKDIR="/dnr"

RUN apk add --no-cache docker

WORKDIR ${WORKDIR}

COPY --from=build ${WORKDIR}/dist/dnr ${WORKDIR}
COPY --from=build ${WORKDIR}/status_template.html ${WORKDIR}

EXPOSE 80 443

ENTRYPOINT ["./dnr"]
CMD ["start"]

FROM release AS dev
LABEL authors="apaes"

RUN apk add --no-cache python3 py3-pip

COPY --from=build ${WORKDIR}/requirements.txt ${WORKDIR}/
RUN pip3 install --break-system-packages -r ${WORKDIR}/requirements.txt

COPY --from=build ${WORKDIR}/main.py ${WORKDIR}/event.py ${WORKDIR}/network.py \
    ${WORKDIR}/nginx.py ${WORKDIR}/status_template.html ${WORKDIR}/

ENTRYPOINT ["python3", "main.py"]
CMD ["start"]
