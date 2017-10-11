# Purpose

This is a sample setup to demonstrate how to use the Orthanc [Serve-Folders](http://book.orthanc-server.com/plugins/serve-folders.html) plugin.

# Description

This demo contains:

- an Orthanc container with the [Serve-Folders plugin](http://book.orthanc-server.com/plugins/serve-folders.html) enabled.

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 8042 on the Docker host (try [http://localhost:8042](http://localhost:8042))

You now have access to 2 new interfaces in Orthanc:

- a Hello world page at [http://localhost:8042/hello-world/index.html](http://localhost:8042/hello-world/index.html)
- a custom version of the Orthanc-Explorer [http://localhost:8042/custom-explorer/explorer.html](http://localhost:8042/custom-explorer/explorer.html).  Note that we have only changed a text on the first page.  You can now modify the orthanc-explorer and adapt it to your needs.