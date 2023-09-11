FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN pip install fastapi==0.103.0
RUN pip install uvicorn[standard]==0.18.2
RUN pip install requests

RUN mkdir /job-service
COPY *.py /job-service

WORKDIR /job-service
CMD ["uvicorn", "job_service:app", "--host", "0.0.0.0", "--port" , "8000"]

