# Purpose

This is a sample setup to demonstrate how one can filter incoming C-Find requests.

On some setup with hundred thousands of studies, we have observed workstations sending
C-Find requests without a single filter criteria.  In that case, Orthanc would have to 
parse it's entire database to respond to the C-Find request and that could take a few minutes
to return a useless results anyway.

This sample will analyze the C-Find requests and make it totaly invalid if it's not "specific" enough.

# Description

This demo contains:

- two orthanc containers that can comunicate in DICOM.
- Orthanc B has installed a lua script to filter the C-Find requests.  Check the `cfind-filter.lua` script in `orthanc-b` folder

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- connect to Orthanc A interface on [http://localhost:8042/app/explorer.html#query-retrieve](http://localhost:8042/app/explorer.html#query-retrieve) and perform the default query on Orthanc B (no criteria)
- check Orthanc B's logs -> you shall see that the query is rejected because it's not specific enough.
- perform a query with 'today' studies only -> this one shall be accepted.
