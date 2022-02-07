# we are using multi-stage build here:
# - first to build the AWS plugin inside a container with a compiler and all dev tools installed
# - then build the orthanc container from an osimis/orthanc image (and copy the AWS plugin from the build container)

####################################################################################################
# this image is a actually a Debian image with developer tools installed such that we can compile the AWS plugin
FROM osimis/orthanc:21.11.0 as orthanc-builder

RUN export DEBIAN_FRONTEND=noninteractive
RUN apt-get --assume-yes update
RUN apt-get --assume-yes install wget
RUN apt-get --assume-yes install build-essential
RUN apt-get --assume-yes install unzip
RUN apt-get --assume-yes install cmake
RUN apt-get --assume-yes install uuid-dev
RUN apt-get --assume-yes install apt-utils
RUN apt-get --assume-yes install libcurl4-openssl-dev
RUN apt-get --assume-yes install curl
RUN apt-get --assume-yes install apt-transport-https
RUN apt-get --assume-yes install liblua5.4-dev
RUN apt-get --assume-yes install libgtest-dev
RUN apt-get --assume-yes install libpng-dev
RUN apt-get --assume-yes install libsqlite3-dev
RUN apt-get --assume-yes install libjpeg-dev zlib1g-dev libdcmtk-dev libboost-all-dev libwrap0-dev libcharls-dev libjsoncpp-dev libpugixml-dev
RUN apt-get --assume-yes install git
RUN apt-get --assume-yes install mercurial
RUN apt-get --assume-yes install zip

# no need to clean apt-cache, it's a build image, we don't care about its size

RUN mkdir -p /sources
RUN mkdir -p /build

# S3 specific prerequisites
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get --allow-releaseinfo-change update && \
    apt-get --assume-yes update && \
    apt-get --assume-yes install libcrypto++-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /sources

# clone the object storage repo and orthanc repo (to get the orthanc framework)
RUN hg clone https://hg.orthanc-server.com/orthanc-object-storage/ -r 1.3.3
RUN hg clone https://hg.orthanc-server.com/orthanc/ -r "Orthanc-1.9.6"

RUN mkdir -p /build/cloud-storage/aws
WORKDIR /build/cloud-storage/aws
RUN cmake -DCMAKE_BUILD_TYPE:STRING=Release -DUSE_VCPKG_PACKAGES=OFF -DORTHANC_FRAMEWORK_SOURCE=path -DORTHANC_FRAMEWORK_ROOT=/sources/orthanc/OrthancFramework/Sources /sources/orthanc-object-storage/Aws/
RUN make -j 4



####################################################################################################
# runtime image for Orthanc

FROM osimis/orthanc:21.11.0

# install packages that are not in the osimis/orthanc public image and that are required to run the AWS S3 plugin
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install libcrypto++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# copy directly to the plugins folder such that we don't need to add a plugins-def.json
COPY --from=orthanc-builder /build/cloud-storage/aws/libOrthancAwsS3Storage.so /usr/share/orthanc/plugins/



RUN mkdir /scripts

RUN ln -s /usr/bin/python3 /usr/bin/python
ENV PYTHONPATH "${PYTHONPATH}:/scripts"

COPY *.py /scripts
COPY *.lua /scripts
