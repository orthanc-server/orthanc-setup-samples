FROM orthancteam/orthanc

RUN apt-get update && apt-get install -y python3-pillow

RUN pip install --break-system-packages decord
RUN pip install --break-system-packages pydicom


COPY convert-mp4-to-cine.py /python/