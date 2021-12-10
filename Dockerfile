# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

RUN mkdir /app

# Copy local code to the container image.
ENV APP_HOME /app

# Update python path
ENV PYTHONPATH="${PYTHONPATH}:src/python"

WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install -r requirements.txt

# Download model
RUN  python -c 'from transformers import AutoModelForQuestionAnswering, AutoTokenizer; \
    token = AutoTokenizer.from_pretrained("etalab-ia/camembert-base-squadFR-fquad-piaf", cache_dir="./models"); \
    token.save_pretrained("./models"); \
    model = AutoModelForQuestionAnswering.from_pretrained("etalab-ia/camembert-base-squadFR-fquad-piaf", cache_dir="./models"); \
    model.save_pretrained("./models")'

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
