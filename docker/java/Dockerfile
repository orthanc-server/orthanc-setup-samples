# you must use the full version to get the Java plugin and the Java SDK
FROM orthancteam/orthanc:24.6.2-full

COPY ExtendingRest.java /java

RUN javac /java/ExtendingRest.java -classpath /java/OrthancJavaSDK.jar