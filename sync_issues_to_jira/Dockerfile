FROM debian:9.5-slim

LABEL "com.github.actions.name"="Sync issues to JIRA"
LABEL "com.github.actions.description"="Sync GitHub issues to JIRA"
LABEL "com.github.actions.icon"="fast-forward"
LABEL "com.github.actions.color"="green"

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && apt-get install -y python3-pip && pip3 install jira PyGithub

RUN apt-get install -y curl && curl -sL https://deb.nodesource.com/setup_11.x | bash -
RUN apt-get install -y nodejs npm && npm i markdown2confluence -g

ADD sync_issue.py /sync_issue.py
ADD sync_pr.py /sync_pr.py
ADD sync_to_jira.py /sync_to_jira.py
ADD test_sync_to_jira.py /test_sync_to_jira.py

ENTRYPOINT ["/usr/bin/python3", "/sync_to_jira.py"]
