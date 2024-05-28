FROM python:3.12.2

WORKDIR /app
COPY ./requirements* .
RUN apt update \
  && pip install --upgrade pip \
  && pip install -U pip setuptools \
  && pip install -r requirements.txt \
