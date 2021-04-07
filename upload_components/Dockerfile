FROM python:3.9-slim-buster

RUN pip install idf-component-manager

COPY upload.sh /upload.sh

ENTRYPOINT  ["/upload.sh"]
