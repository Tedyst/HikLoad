FROM python:3.9.7
LABEL org.opencontainers.image.source https://github.com/Tedyst/HikLoad

WORKDIR /app
RUN pip install pipenv
COPY Pipfile Pipfile.lock .
RUN pipenv install --deploy

ENV RUNNING_IN_DOCKER TRUE
COPY main.py setup.py README.md /app/
COPY hikload /app/hikload
ENTRYPOINT ["python", "main.py"]