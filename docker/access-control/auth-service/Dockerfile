FROM python:3.10

ENV PYTHONUNBUFFERED=1

RUN pip install fastapi==0.78.0
RUN pip install uvicorn[standard]==0.18.2
RUN pip install orthanc-api-client==0.5.8

RUN mkdir /auth-service
COPY *.py /auth-service/

WORKDIR /auth-service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port" , "8000"]