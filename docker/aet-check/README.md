To start, use `docker-compose up`.

As described in the `docker-compose.yml` file, three Orthanc servers are
reachable via HTTP on ports 80 (foo), 81 (bar) and 82 (baz) on the
Docker host.

Foo knows about bar and baz, but neither bar nor baz knows about any
other instances.

When talking to bar, foo calls it "BAZ", and when talking to baz, foo
calls it "BAR". By default, Orthanc doesn't care, and bar accepts
associations from foo even though it is not using the correct AET.
However, when setting "DicomCheckCalledAet" to true, Orthanc refuses
associations, as demonstrated by baz.
