FROM python:3.12

RUN pip install --break-system-packages orthanc-api-client==0.21.0

COPY populate.py /

CMD [ "python", "/populate.py" ]