# docker build -t orthancteam/pynetdicom-echo-scp-with-tls .
# docker push orthancteam/pynetdicom-echo-scp-with-tls
# on the test machine:
# docker pull orthancteam/pynetdicom-echo-scp-with-tls
# mkdir -p /tls
# openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tls/privkey.pem -out /tls/cert.pem -subj "/C=BE/CN=178.32.150.5"
# docker run -p 11112:11112 -v /tls:/tls -e IGNORE_UNEXPECTED_EOF=1 -e DICOM_AET=TEST -e PRIVATE_KEY=/tls/privkey.pem -e CERTIFICATE=/tls/cert.pem  orthancteam/pynetdicom-echo-scp-with-tls

FROM python:3.12

RUN pip install --break-system-packages pydicom pynetdicom

ENV PYTHONUNBUFFERED=1
COPY pydicom-tls.py /scripts/

CMD ["python", "/scripts/pydicom-tls.py"]