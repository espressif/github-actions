FROM python:3.10-bullseye

RUN pip install idf-component-manager~=1.1

COPY upload.sh /upload.sh

ENTRYPOINT  ["/upload.sh"]
