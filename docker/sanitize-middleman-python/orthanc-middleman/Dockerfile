FROM orthancteam/orthanc

RUN pip3 install --break-system-packages requests

ENV VERBOSE_STARTUP=true
ENV VERBOSE_ENABLED=true
COPY orthanc.json /etc/orthanc/
COPY *.py /python/
