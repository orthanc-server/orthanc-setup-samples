FROM python:3.12
ENV PYTHONUNBUFFERED=1

RUN pip install --break-system-packages orthanc-api-client==0.21.0 orthanc-tools==0.17.7
RUN pip install --break-system-packages pandas matplotlib

COPY benchmark-db.py /

CMD [ "python", "/benchmark-db.py" ]