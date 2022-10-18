FROM python:3.10-bullseye

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

COPY requirements.txt /tmp/

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git && \
    pip3 install --upgrade pip && \
    pip3 install -r /tmp/requirements.txt

COPY entrypoint.sh /
COPY update_submodule_versions.py /

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
