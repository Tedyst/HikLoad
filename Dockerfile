FROM python:3.6-alpine

ENV server "192.168.1.69"
ENV cameras "101 201"
ENV user "admin"
ENV password ""
ENV PYTHONUNBUFFERED "1"
ENV downloadPath "/data/"
ENV PYTHONPATH /

VOLUME /data

RUN apk add --no-cache ffmpeg
COPY hikload /hikload
COPY requirements.txt /hikload
COPY hikload/__init__.py /
WORKDIR /hikvision
RUN ["pip", "install", "-r", "/hikload/requirements.txt"]
CMD ["python3", "/hikload/main.py"]