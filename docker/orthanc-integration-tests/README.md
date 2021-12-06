# Purpose

This is a sample setup to demonstrate how to run the [Orthanc integration tests](https://hg.orthanc-server.com/orthanc-tests) with a custom version of Orthanc.

# Description

This demo contains:

- an Orthanc container that you want to test (orthanc-under-tests).
- an Orthanc container with the Orthanc integration tests (orthanc-tests)

# Starting the setup

To test a release condidate:
- first build the release candidate docker image (from orthanc-builder repo)
- run each test individually:

```
COMPOSE_FILE=docker-compose.sqlite.yml                   docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit

COMPOSE_FILE=docker-compose.odbc-sql-server.yml          docker-compose down -v
COMPOSE_FILE=docker-compose.odbc-sql-server.yml          docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit

COMPOSE_FILE=docker-compose.odbc-postgres.yml            docker-compose down -v
COMPOSE_FILE=docker-compose.odbc-postgres.yml            docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit

COMPOSE_FILE=docker-compose.odbc-sqlite.yml              docker-compose down -v
COMPOSE_FILE=docker-compose.odbc-sqlite.yml              docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit

COMPOSE_FILE=docker-compose.postgres.yml                 docker-compose down -v
COMPOSE_FILE=docker-compose.postgres.yml                 docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit

COMPOSE_FILE=docker-compose.mysql.yml                    docker-compose down -v
COMPOSE_FILE=docker-compose.mysql.yml                    docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit

# note: not functional yet:
COMPOSE_FILE=docker-compose.odbc-mysql.yml               docker-compose down -v
COMPOSE_FILE=docker-compose.odbc-mysql.yml               docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit
```
