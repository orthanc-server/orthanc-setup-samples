FROM python:3.12
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /
RUN pip install --break-system-packages -r /requirements.txt

COPY benchmark-db.py /

CMD [ "python", "/benchmark-db.py" ]