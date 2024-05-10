FROM python:3.12.3-alpine3.19

ENV APP_PATH /app/csa_be
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR ${APP_PATH}

COPY . ${APP_PATH}

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000