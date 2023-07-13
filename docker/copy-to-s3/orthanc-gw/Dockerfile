FROM osimis/orthanc:23.7.0

ENV PYTHONUNBUFFERED=1
RUN pip install orthanc-api-client==0.13.5
RUN pip install boto3

RUN mkdir -p /scripts
COPY *.py /scripts

ENV ORTHANC__PYTHON_SCRIPT=/scripts/plugin.py