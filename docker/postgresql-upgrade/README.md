# Purpose

This is a sample setup to demonstrate how to upgrade a PostgreSQL database that is used by Orthanc.

# Description

This demo contains:

- an Orthanc container
- a PostgreSQL v10 that is used by Orthanc in a first time
- a PostgreSQL v15 that is used by Orthanc in a second time

# Starting the setup

To start the setup, type: 
```
docker compose pull
docker compose up -d
```

At the beginning, Orthanc uses PostgreSQL v 10 as its DB engine

# demo

- upload a few files in [Orthanc UI](http://localhost:8042)
- stop Orthanc service to prepare for the DB upgrade to v 15.
  ```
  docker compose stop orthanc
  ```
- dump the DB v 10 in the /backup volume.  Note: this is performed with pg_dump from v 15 and therefore from the
  `orthanc-index-15` container
  ```
  docker compose exec -d orthanc-index-15 bash -c "pg_dump --dbname=postgresql://postgres:postgres@orthanc-index-10:5432/postgres -Fc | gzip > /backup/dump10from15.gz"
  ```
- wait for the backup to complete by monitoring the size of the backup file and/ or looking for the pg_dump process
  ```
  docker compose exec orthanc-index-15 bash -c "ls -al /backup"
  docker compose exec orthanc-index-15 bash -c "ps -a | grep pg_dump"
  ```
- once the backup is complete, restore the backup in DB v 15
  ```
  docker compose exec -d orthanc-index-15 bash -c "dropdb --if-exists -U postgres postgres && createdb -U postgres postgres && gunzip < /backup/dump10from15.gz | pg_restore -U postgres -d postgres"
  ```
- wait for the backup to complete by monitoring the pg_restore process
  ```
  docker compose exec orthanc-index-15 bash -c "ps -a | grep pg_restore"
  ```

- modify the `docker-compose.yml` such that Orthanc now references the DB v 15:
  ```
    # depends_on: [orthanc-index-10]
    depends_on: [orthanc-index-15]
    # ORTHANC__POSTGRESQL__HOST: "orthanc-index-10"
    ORTHANC__POSTGRESQL__HOST: "orthanc-index-15"
  ```

- restart Orthanc which will now be connected to the DB v 15:
  ```
  docker compose up -d
  ```
- connect to the [Orthanc UI](http://localhost:8042) and validate that the content is still accessible.
- once you consider that the upgrade was successful, you may remove the `orthanc-index-10` from docker-compose and delete its volume
  ```
  docker volume ls | grep orthanc-index-10
  docker volume rm postgresql-upgrade_orthanc-index-10
  ```
