# Purpose

This is a sample setup to demonstrate how to transition from SQLite to PostgreSQL database
by using the [Advanced Storage plugin](https://book.orthanc-server.com/plugins/advanced-storage.html).

# Description

This demo contains:

- an Orthanc container configured to use the default SQLite DB.
- an Orthanc container with the [PostgreSQL plugin](https://book.orthanc-server.com/plugins/postgresql.html) 
  and the [Advanced Storage plugin](https://book.orthanc-server.com/plugins/advanced-storage.html) enabled.
- a PostgreSQL container that will store the Orthanc Index DB (the dicom files are stored in a Docker volume)

# demo

Only one Orthanc can run at a time since they use the same ports.

- Start the setup with:
  ```
  docker compose up orthanc-sqlite
  ```

- Upload a few studies through the UI on [http://localhost:8043/ui/app/](http://localhost:8043/ui/app/)

- Stop the Orthanc instance that is using SQLite and start the PG one.  Note: the PG Orthanc
  is replacing the SQLite and is accessible at the same url: [http://localhost:8043/ui/app/](http://localhost:8043/ui/app/) 
  ```
  docker compose down orthanc-sqlite
  docker compose up orthanc-pg
  ```

- The Indexer will index the files from the SQLite Orthanc and will
  take the ownership.  If, at this point, you delete a study, you
  should see its files removed from the `orthanc-files-for-sqlite` volume.

- If you ingest a new study now, you should see it appear in the 
  `orthanc-files-for-pg` volume.

- Then, consider that you want to re-organize your storage and
  make it more [user-friendly](https://book.orthanc-server.com/plugins/advanced-storage.html#customizing-paths).  
  You can potentially start yet another
  Orthanc instance with the housekeeper plugin.  It should then reprocess the whole database and move
  the files from the previous  `orthanc-files-for-sqlite` storage to the new volume `orthanc-files-for-pg`.  
  You should then have no files left in the `orthanc-files-for-sqlite` volume. 
  **Note:** You'll need a Housekeeper plugin version higher than 1.12.8+
  to support the `ForceReconstructFiles` option.

  ```
  docker compose down orthanc-pg
  docker compose up orthanc-pg-hk
  ```
