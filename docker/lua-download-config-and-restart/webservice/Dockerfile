FROM python:3.10

WORKDIR /code

RUN pip install fastapi
RUN pip install "uvicorn[standard]"

COPY main.py /code/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]