FROM python:3.9

RUN pip install orthanc-api-client==0.5.8

COPY populate.py /

CMD [ "python", "/populate.py" ]