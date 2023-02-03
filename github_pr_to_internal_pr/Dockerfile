FROM node:current-bullseye-slim

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

COPY requirements.txt /tmp/

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git && \
    apt-get install -y python3-pip && \
    pip3 install --upgrade pip && \
    pip3 install -r /tmp/requirements.txt

# Error: fatal: detected dubious ownership in repository at '/github/workspace'
#      To add an exception for this directory, call:
#          git config --global --add safe.directory /github/workspace
# Reason: Recent versions of git require the .git folder to be owned
# by the same user (see https://github.blog/2022-04-12-git-security-vulnerability-announced/).
# Related
# - https://github.com/actions/runner/issues/2033
# - https://github.com/actions/checkout/issues/1048
# - https://github.com/actions/runner-images/issues/6775
RUN git config --system --add safe.directory /github/workspace

COPY github_pr_to_internal_pr.py /

ENTRYPOINT ["/usr/bin/python3", "/github_pr_to_internal_pr.py"]
