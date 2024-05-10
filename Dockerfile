FROM python:3.12.3-alpine3.19

ENV APP_PATH /app/csa_be

WORKDIR ${APP_PATH}

COPY . ${APP_PATH}

RUN pip install -r requirements.txt

EXPOSE 8000