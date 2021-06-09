FROM node:current-buster-slim

LABEL "com.github.actions.name"="Sync issues to JIRA"
LABEL "com.github.actions.description"="Sync GitHub issues to JIRA"
LABEL "com.github.actions.icon"="fast-forward"
LABEL "com.github.actions.color"="green"

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ADD requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get install -y python3-pip && pip3 install -r /tmp/requirements.txt

RUN rm /tmp/requirements.txt

RUN npm i -g @shogobg/markdown2confluence@0.1.0

ADD sync_issue.py /sync_issue.py
ADD sync_pr.py /sync_pr.py
ADD sync_to_jira.py /sync_to_jira.py
ADD test_sync_to_jira.py /test_sync_to_jira.py
ADD push_event.py /push_event.py

ENTRYPOINT ["/usr/bin/python3", "/sync_to_jira.py"]
