FROM python:3.9-slim-buster

RUN apt-get update && apt-get install -y p7zip-full git && pip install PyGithub

ADD release_zips.py /release_zips.py

ENTRYPOINT ["python", "/release_zips.py"]
