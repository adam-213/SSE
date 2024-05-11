# Use an official Python image.
FROM python:3.12-slim
LABEL authors="Adam"

# Set app workdir
WORKDIR /app
ADD . /app

# Setup env
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 8000

# Tell python that its running in docker to look in specific paths
ENV RUNNING_IN_DOCKER true
ENV NAME LogParser

# Run it
ENTRYPOINT ["python", "Parser.py"]