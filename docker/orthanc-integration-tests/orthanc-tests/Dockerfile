# mercurial does not work anymore on jodogne/orthanc-tests -> use a specific image
FROM ubuntu:20.04 as ubuntu-hg
RUN apt-get update
RUN	DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install mercurial

WORKDIR /
RUN hg clone https://hg.orthanc-server.com/orthanc-tests/ -r "Orthanc-1.9.7"


FROM jodogne/orthanc-tests
RUN mkdir /tests
WORKDIR /tests

COPY --from=ubuntu-hg /orthanc-tests /tests/orthanc-tests
RUN ls -al /tests/
RUN mkdir /tmp/orthanc-tests/

RUN mkdir /scripts
COPY wait-for-it.sh /scripts

ENTRYPOINT /scripts/wait-for-it.sh orthanc-under-tests:8042 -t 60 && python /tests/orthanc-tests/Tests/Run.py --server=orthanc-under-tests --force --docker -- -v
