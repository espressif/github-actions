FROM python:3.10-bullseye

RUN pip install idf-component-manager~=1.0.0

COPY upload.sh /upload.sh

ENTRYPOINT  ["/upload.sh"]
