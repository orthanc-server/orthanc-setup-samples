FROM python:3.12

ENV PYTHONUNBUFFERED=1

RUN pip install fastapi==0.109.1
RUN pip install uvicorn[standard]==0.18.2
RUN pip install orthanc-api-client==0.21.0

RUN mkdir /auth-service
COPY *.py /auth-service/

WORKDIR /auth-service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port" , "8000"]