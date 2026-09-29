FROM orthancteam/orthanc

ENV PYTHONUNBUFFERED=1
RUN pip install --break-system-packages orthanc-api-client==0.25.3
RUN pip install --break-system-packages boto3

RUN mkdir -p /scripts
COPY *.py /scripts

ENV ORTHANC__PYTHON_SCRIPT=/scripts/plugin.py