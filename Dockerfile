FROM python:3.9.7
LABEL org.opencontainers.image.source https://github.com/Tedyst/HikLoad

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

ENV RUNNING_IN_DOCKER TRUE
COPY main.py setup.py README.md /app/
COPY hikload /app/hikload
ENTRYPOINT ["python", "main.py"]