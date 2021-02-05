FROM python:3.7-slim

RUN apt-get update \
&& apt-get install gcc make -y \
&& apt-get clean

COPY . /app

WORKDIR /app

RUN pip3 install -r requirements.txt

ENTRYPOINT uvicorn main:app --host 0.0.0.0 --port 80 --proxy-headers

EXPOSE 80