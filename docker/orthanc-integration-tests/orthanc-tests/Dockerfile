FROM jodogne/orthanc-tests

RUN mkdir /tests
WORKDIR /tests

# clone the right version for Orthanc-1.4.2-mainline-20181030
RUN wget https://bitbucket.org/sjodogne/orthanc-tests/get/Orthanc-1.5.8.zip --output-document /tmp/orthanc-tests.zip
RUN mkdir /tmp/orthanc-tests/
RUN mkdir /tests/orthanc-tests/

RUN unzip /tmp/orthanc-tests.zip -d /tmp/
RUN mv /tmp/sjodogne-orthanc-tests*/* /tests/orthanc-tests/
RUN mkdir /scripts
COPY wait-for-it.sh /scripts
ENTRYPOINT /scripts/wait-for-it.sh orthanc-under-tests:8042 -t 20 && python /tests/orthanc-tests/Tests/Run.py --server=orthanc-under-tests --force --docker -- -v
