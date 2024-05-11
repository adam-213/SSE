# Use an official Python image.
FROM python:3.12-slim
LABEL authors="Adam"

# Setup non root user
RUN groupadd -r myusergroup && useradd -r -g myusergroup -u 1001 myuser

# Set app workdir
WORKDIR /app
# copy py_files + requirements in with making the new user as the owner
COPY --chown=myuser:myusergroup . /app

# Setup env
RUN pip install --no-cache-dir -r requirements.txt

ENV NAME LogParser
# Switch the user to the new user
USER myuser

# Run it
ENTRYPOINT ["python", "Parser.py"]