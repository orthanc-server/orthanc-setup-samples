# Purpose

This is a sample setup to demonstrate how to run orthanc with the advanced storage plugin (currently in beta).
DISCLAIMER: this should not be used in production right now since it requires a modification of the DB schema and
there is no downgrade path !

# Description

This demo contains:

- an orthanc container with the Advanced Storage plugin enabled
- a Postgresql container to store the Orthanc database

# Starting the setup

To start the setup, type: `docker compose up`

# demo

- Orthanc is accessible at [http://localhost:8044/ui/app/](http://localhost:8044/ui/app/)


# Plugin configuration doc (waiting it is moved to the orthanc book)

```json
    {
        "AdvancedStorage": {
        
            // Enables/disables the plugin
            "Enable": false,

            // Enables/disables support for multiple StorageDirectories
            "MultipleStorages" : {
                "Storages" : {
                // Only the storage id is stored in the SQL DB for each file, not the storage path.
                // Therefore, storage path may change in case you move your data from one place to another.
                // The storgae ids may never change since they are stored in DB; you can only add new ones.
                "1" : "/var/lib/orthanc/db",
                "2" : "/mnt/disk2/orthanc"
                },

                // The storage on which new data is stored.
                // There's currently no automatic changes of disks
                "CurrentStorage" : "2",
            },

            // Defines the storage structure and file namings.  
            // These keywords can be used to generate the path:
            // Attachment info:
            //   {UUID}                           : A unique file identifier
            //   {01(UUID)}                       : The first 2 characters of the file UUID
            //   {23(UUID)}                       : The 3rd and 4th characters of the file UUID
            //   {.ext}                           : The file extension
            // DICOM TAGS:
            //   {PatientID}, {PatientName}, {PatientBirthDate}
            //   {StudyInstanceUID}, {SeriesInstanceUID}, {SOPInstanceUID}
            //   {StudyDescription}, {SeriesDescription}
            //   {StudyDate}, {AccessionNumber}, {InstanceNumber}, {SeriesNumber}
            // Transformed DICOM TAGS:
            //   {split(StudyDate)}               : 3 subfolders: YYYY/MM/DD
            //   {split(PatientBirthDate)}        : 3 subfolders: YYYY/MM/DD
            //   {pad4(InstanceNumber)}           : the instance number padded with zeroes to have 4 characters
            //   {pad4(SeriesNumber)}             : the instance number padded with zeroes to have 4 characters
            //   {pad6(InstanceNumber)}           : the instance number padded with zeroes to have 6 characters
            //   {pad6(SeriesNumber)}             : the instance number padded with zeroes to have 6 characters
            //   {pad8(InstanceNumber)}           : the instance number padded with zeroes to have 8 characters
            //   {pad8(SeriesNumber)}             : the instance number padded with zeroes to have 8 characters
            // Orthanc IDs:
            //   {OrthancPatientID}, {OrthancStudyID}, {OrthancSeriesID}, {OrthancInstanceID}
            // Transformed Orthanc IDs:
            //   {01(OrthancPatientID)}, {01(OrthancStudyID)}, ...  : the first 2 characters of the Orthanc ID
            //   {23(OrthancPatientID)}, {23(OrthancStudyID)}, ...  : the 3rd and 4th characters of the Orthanc ID
            // Examples:
            // "OrthancDefault"                         is a special value to use the same structure as the Orthanc core.  
            //                                          This option consumes less space in the SQL DB since the path must not be saved in DB.
            // "{01(UUID)}/{23(UUID)}/{UUID}{.ext}"     is equivalent with the structure of the Orthanc core with and added file extension
            // "{split(StudyDate)}/{StudyInstanceUID} - {PatientID}/{SeriesInstanceUID}/{pad6(InstanceNumber)} - {UUID}{.ext}"
            // "{PatientID} - {PatientName}/{StudyDate} - {StudyInstanceUID} - {StudyDescription}/{SeriesInstanceUID}/{UUID}{.ext}"
            // Notes:
            // - To prevent files from being overwritten, it is very important that their path is unique !
            //   Therefore, your NamingScheme must always include:
            //   - either the file {UUID} (this is mandatory in this Beta version !!!!!)
            //   - MAYBE IN A LATER BETA VERSION: at least a patient identifier {PatientID} or {OrthancPatientID},
            //     a study identifier {StudyInstanceUID} or {OrthancStudyID},
            //     a series identifier {SeriesInstanceUID} or {OrthancSeriesID},
            //     an instance identifier {SOPInstanceUID} or {OrthancInstanceID}
            // - The NamingScheme defines a RELATIVE path to either the "StorageDirectory" of Orthanc or one of
            //   the "MultipleStorages" of this plugin.
            // - The relative path generated from the NamingScheme is stored in the SQL DB.  Therefore, you may change the
            //   NamingScheme at any time and you'll still be able to access previously saved files.
            "NamingScheme" : "OrthancDefault",

            // Defines the maximum length for path used in the storage.  If a file is longer
            // than this limit, it is stored with the default orthanc naming scheme
            // (and a warning is issued).
            // Note, on Windows, the maximum path length is 260 bytes by default but can be increased
            // through a configuration.
            "MaxPathLength" : 256,

            // When saving non DICOM attachments, Orthanc does not have access to the DICOM tags
            // and can therefore not compute a path using the NamingScheme.
            // Therefore, all non DICOM attachements are grouped in a subfolder using the 
            // legacy structure.  With this option, you can define a root folder for these 
            // non DICOM attachments
            // e.g: "OtherAttachmentsPrefix": "_attachments"
            // Notes:
            // - When using a prefix, the path is saved in the SQL DB.  Therefore, you may change the OtherAttachmentsPrefix
            // at any time and you'll still be able to access previously saved files.
            "OtherAttachmentsPrefix": ""
        }
    }

```