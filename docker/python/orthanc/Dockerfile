FROM orthancteam/orthanc

# This example is using a virtual env that is not mandatory when using Docker containers
# but recommended since python 3.11 and Debian bookworm based images where you get a warning
# when installing system-wide packages.
RUN apt-get update && apt install -y python3-venv
RUN python3 -m venv /.venv

RUN /.venv/bin/pip install pydicom
ENV PYTHONPATH=/.venv/lib64/python3.11/site-packages/

RUN mkdir /python
COPY * /python/
