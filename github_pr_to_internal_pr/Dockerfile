FROM node:current-bullseye-slim

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ADD requirements.txt /tmp/requirements.txt

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git && \
    apt-get install -y python3-pip && \
    pip3 install -r /tmp/requirements.txt

RUN rm /tmp/requirements.txt

ADD github_pr_to_internal_pr.py /github_pr_to_internal_pr.py

ENTRYPOINT ["/usr/bin/python3", "/github_pr_to_internal_pr.py"]
