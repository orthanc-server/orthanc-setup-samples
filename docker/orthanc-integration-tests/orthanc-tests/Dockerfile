FROM jodogne/orthanc-tests

RUN mkdir /tests
WORKDIR /tests

# clone the right version for Orthanc-1.4.1
RUN hg clone -r b6b207b https://bitbucket.org/sjodogne/orthanc-tests 
RUN mkdir /scripts
COPY wait-for-it.sh /scripts
ENTRYPOINT /scripts/wait-for-it.sh orthanc-under-tests:8042 -t 20 && python /tests/orthanc-tests/Tests/Run.py --server=orthanc-under-tests --force --docker -- -v
