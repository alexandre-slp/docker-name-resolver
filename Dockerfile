FROM python:3.12-alpine AS build
LABEL authors="apaes"

RUN apk add --no-cache binutils
RUN apk upgrade --no-cache

ENV WORKDIR="/dnr"

WORKDIR ${WORKDIR}

COPY requirements.txt main.py event.py network.py nginx.py status_template.html ${WORKDIR}

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pyinstaller --onefile --clean --noconfirm --name=dnr main.py

FROM nginx:1.29-alpine-slim AS release
LABEL authors="apaes"

ENV WORKDIR="/dnr"

RUN apk upgrade --no-cache

RUN addgroup -S dnr && adduser -S -G dnr dnr

RUN rm -f /etc/nginx/conf.d/default.conf
RUN sed -i 's/^[[:space:]]*user nginx;/# user nginx;/' /etc/nginx/nginx.conf

WORKDIR ${WORKDIR}

COPY --from=build ${WORKDIR}/dist/dnr ${WORKDIR}
COPY --from=build ${WORKDIR}/status_template.html ${WORKDIR}

RUN chown -R dnr:dnr \
    ${WORKDIR} \
    /etc/nginx/conf.d \
    /usr/share/nginx/html \
    /var/cache/nginx \
    /run \
    /var/run \
    /var/log/nginx

EXPOSE 8080

USER dnr

ENTRYPOINT ["./dnr"]
CMD ["start"]

FROM release AS dev
LABEL authors="apaes"

USER root

RUN apk add --no-cache python3 py3-pip

COPY --from=build ${WORKDIR}/requirements.txt ${WORKDIR}/
RUN pip3 install --break-system-packages -r ${WORKDIR}/requirements.txt

COPY --from=build ${WORKDIR}/main.py ${WORKDIR}/event.py ${WORKDIR}/network.py \
    ${WORKDIR}/nginx.py ${WORKDIR}/status_template.html ${WORKDIR}/

RUN chown -R dnr:dnr ${WORKDIR}

USER dnr

ENTRYPOINT ["python3", "main.py"]
CMD ["start"]
