FROM node:current-bullseye-slim

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ADD requirements.txt /tmp/requirements.txt

RUN apt-get update \
 && apt-get install -y python3-pip \
 && pip3 install --upgrade pip \
 && pip3 install -r /tmp/requirements.txt

RUN rm /tmp/requirements.txt

RUN npm i -g @shogobg/markdown2confluence@0.1.6

ADD sync_issue.py /sync_issue.py
ADD sync_pr.py /sync_pr.py
ADD sync_to_jira.py /sync_to_jira.py
ADD test_sync_to_jira.py /test_sync_to_jira.py

ENTRYPOINT ["/usr/bin/python3", "/sync_to_jira.py"]
