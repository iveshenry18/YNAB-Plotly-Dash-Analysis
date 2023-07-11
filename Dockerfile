# A dockerfile for python 3.11 on ubuntu that serves a plotly dash app

FROM python:3.11-slim

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . ./
CMD gunicorn -b 0.0.0.0:80 app.app:server