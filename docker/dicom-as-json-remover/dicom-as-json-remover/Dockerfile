FROM python:3.11

RUN pip install boto3
RUN pip install psycopg2
RUN pip install orthanc-tools==0.12.14

RUN mkdir /scripts
COPY *.py /scripts/

ENV PYTHONUNBUFFERED=1

WORKDIR /scripts
CMD ["python", "-u", "/scripts/dicom-as-json-remover.py"]


