# docker build -t orthancteam/detect-duplicates:v1 .

FROM python:3.12

RUN pip install --break-system-packages psycopg2
RUN pip install --break-system-packages orthanc-api-client

COPY resolve-duplicates.py /

CMD ["python", "/resolve-duplicates.py"]