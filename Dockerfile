FROM python:3.10
LABEL org.opencontainers.image.source https://github.com/Tedyst/HikLoad

WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv requirements > requirements.txt &&\
    sed -i '/pyqt5/d' requirements.txt &&\
    apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt

ENV RUNNING_IN_DOCKER TRUE
COPY main.py setup.py README.md /app/
COPY hikload /app/hikload
ENTRYPOINT ["python", "main.py"]