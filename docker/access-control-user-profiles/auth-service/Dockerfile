FROM python:3.12

ENV PYTHONUNBUFFERED=1

RUN pip install pydantic==2.10.6
RUN pip install fastapi
RUN pip install uvicorn[standard]
RUN pip install pyjwt[crypto]==2.6.0
RUN pip install pytz

RUN mkdir /auth-service
COPY *.py /auth-service/

WORKDIR /auth-service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port" , "8000"]