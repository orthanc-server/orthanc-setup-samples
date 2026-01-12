# SPDX-FileCopyrightText: 2020-2023 Osimis S.A., 2024-2025 Orthanc Team SRL, 2021-2025 Sebastien Jodogne, ICTEAM UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

##
## Python plugin for Orthanc
## Copyright (C) 2020-2023 Osimis S.A., Belgium
## Copyright (C) 2024-2025 Orthanc Team SRL, Belgium
## Copyright (C) 2021-2025 Sebastien Jodogne, ICTEAM UCLouvain, Belgium
##
## This program is free software: you can redistribute it and/or
## modify it under the terms of the GNU Affero General Public License
## as published by the Free Software Foundation, either version 3 of
## the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##


# WARNING: Auto-generated file. Do not modify it by hand.


import typing



class ChangeType():
    """
    The supported types of changes that can be signaled to the change callback. Note: This enumeration is not used to store changes in the database!
    """

    """
    Series is now complete
    """
    COMPLETED_SERIES: int = 0,

    """
    Deleted resource
    """
    DELETED: int = 1,

    """
    A new instance was added to this resource
    """
    NEW_CHILD_INSTANCE: int = 2,

    """
    New instance received
    """
    NEW_INSTANCE: int = 3,

    """
    New patient created
    """
    NEW_PATIENT: int = 4,

    """
    New series created
    """
    NEW_SERIES: int = 5,

    """
    New study created
    """
    NEW_STUDY: int = 6,

    """
    Timeout: No new instance in this patient
    """
    STABLE_PATIENT: int = 7,

    """
    Timeout: No new instance in this series
    """
    STABLE_SERIES: int = 8,

    """
    Timeout: No new instance in this study
    """
    STABLE_STUDY: int = 9,

    """
    Orthanc has started
    """
    ORTHANC_STARTED: int = 10,

    """
    Orthanc is stopping
    """
    ORTHANC_STOPPED: int = 11,

    """
    Some user-defined attachment has changed for this resource
    """
    UPDATED_ATTACHMENT: int = 12,

    """
    Some user-defined metadata has changed for this resource
    """
    UPDATED_METADATA: int = 13,

    """
    The list of Orthanc peers has changed
    """
    UPDATED_PEERS: int = 14,

    """
    The list of DICOM modalities has changed
    """
    UPDATED_MODALITIES: int = 15,

    """
    New Job submitted
    """
    JOB_SUBMITTED: int = 16,

    """
    A Job has completed successfully
    """
    JOB_SUCCESS: int = 17,

    """
    A Job has failed
    """
    JOB_FAILURE: int = 18,

class CompressionType():
    """
    The compression algorithms that are supported by the Orthanc core.
    """

    """
    Standard zlib compression
    """
    ZLIB: int = 0,

    """
    zlib, prefixed with uncompressed size (uint64_t)
    """
    ZLIB_WITH_SIZE: int = 1,

    """
    Standard gzip compression
    """
    GZIP: int = 2,

    """
    gzip, prefixed with uncompressed size (uint64_t)
    """
    GZIP_WITH_SIZE: int = 3,

    """
    No compression (new in Orthanc 1.12.8)
    """
    NONE: int = 4,

class ConstraintType():
    """
    The constraints on the tags (main DICOM tags and identifier tags) that must be supported by the database plugins.
    """

    """
    Equal
    """
    EQUAL: int = 1,

    """
    Less or equal
    """
    SMALLER_OR_EQUAL: int = 2,

    """
    More or equal
    """
    GREATER_OR_EQUAL: int = 3,

    """
    Wildcard matching
    """
    WILDCARD: int = 4,

    """
    List of values
    """
    LIST: int = 5,

class ContentType():
    """
    The content types that are supported by Orthanc plugins.
    """

    """
    Unknown content type
    """
    UNKNOWN: int = 0,

    """
    DICOM
    """
    DICOM: int = 1,

    """
    JSON summary of a DICOM file
    """
    DICOM_AS_JSON: int = 2,

    """
    DICOM Header till pixel data
    """
    DICOM_UNTIL_PIXEL_DATA: int = 3,

class CreateDicomFlags():
    """
    Flags for the creation of a DICOM file.
    """

    """
    Default mode
    """
    NONE: int = 0,

    """
    Decode fields encoded using data URI scheme
    """
    DECODE_DATA_URI_SCHEME: int = 1,

    """
    Automatically generate DICOM identifiers
    """
    GENERATE_IDENTIFIERS: int = 2,

class DicomToJsonFlags():
    """
    Flags to customize a DICOM-to-JSON conversion. By default, binary tags are formatted using Data URI scheme.
    """

    """
    Default formatting
    """
    NONE: int = 0,

    """
    Include the binary tags
    """
    INCLUDE_BINARY: int = 1,

    """
    Include the private tags
    """
    INCLUDE_PRIVATE_TAGS: int = 2,

    """
    Include the tags unknown by the dictionary
    """
    INCLUDE_UNKNOWN_TAGS: int = 4,

    """
    Include the pixel data
    """
    INCLUDE_PIXEL_DATA: int = 8,

    """
    Output binary tags as-is, dropping non-ASCII
    """
    CONVERT_BINARY_TO_ASCII: int = 16,

    """
    Signal binary tags as null values
    """
    CONVERT_BINARY_TO_NULL: int = 32,

    """
    Stop processing after pixel data (new in 1.9.1)
    """
    STOP_AFTER_PIXEL_DATA: int = 64,

    """
    Skip tags whose element is zero (new in 1.9.1)
    """
    SKIP_GROUP_LENGTHS: int = 128,

class DicomToJsonFormat():
    """
    The possible output formats for a DICOM-to-JSON conversion.
    """

    """
    Full output, with most details
    """
    FULL: int = 1,

    """
    Tags output as hexadecimal numbers
    """
    SHORT: int = 2,

    """
    Human-readable JSON
    """
    HUMAN: int = 3,

class DicomWebBinaryMode():
    """
    The available modes to export a binary DICOM tag into a DICOMweb JSON or XML document.
    """

    """
    Don't include binary tags
    """
    IGNORE: int = 0,

    """
    Inline encoding using Base64
    """
    INLINE_BINARY: int = 1,

    """
    Use a bulk data URI field
    """
    BULK_DATA_URI: int = 2,

class ErrorCode():
    """
    The various error codes that can be returned by the Orthanc core.
    """

    """
    Internal error
    """
    INTERNAL_ERROR: int = -1,

    """
    Success
    """
    SUCCESS: int = 0,

    """
    Error encountered within the plugin engine
    """
    PLUGIN: int = 1,

    """
    Not implemented yet
    """
    NOT_IMPLEMENTED: int = 2,

    """
    Parameter out of range
    """
    PARAMETER_OUT_OF_RANGE: int = 3,

    """
    The server hosting Orthanc is running out of memory
    """
    NOT_ENOUGH_MEMORY: int = 4,

    """
    Bad type for a parameter
    """
    BAD_PARAMETER_TYPE: int = 5,

    """
    Bad sequence of calls
    """
    BAD_SEQUENCE_OF_CALLS: int = 6,

    """
    Accessing an inexistent item
    """
    INEXISTENT_ITEM: int = 7,

    """
    Bad request
    """
    BAD_REQUEST: int = 8,

    """
    Error in the network protocol
    """
    NETWORK_PROTOCOL: int = 9,

    """
    Error while calling a system command
    """
    SYSTEM_COMMAND: int = 10,

    """
    Error with the database engine
    """
    DATABASE: int = 11,

    """
    Badly formatted URI
    """
    URI_SYNTAX: int = 12,

    """
    Inexistent file
    """
    INEXISTENT_FILE: int = 13,

    """
    Cannot write to file
    """
    CANNOT_WRITE_FILE: int = 14,

    """
    Bad file format
    """
    BAD_FILE_FORMAT: int = 15,

    """
    Timeout
    """
    TIMEOUT: int = 16,

    """
    Unknown resource
    """
    UNKNOWN_RESOURCE: int = 17,

    """
    Incompatible version of the database
    """
    INCOMPATIBLE_DATABASE_VERSION: int = 18,

    """
    The file storage is full
    """
    FULL_STORAGE: int = 19,

    """
    Corrupted file (e.g. inconsistent MD5 hash)
    """
    CORRUPTED_FILE: int = 20,

    """
    Inexistent tag
    """
    INEXISTENT_TAG: int = 21,

    """
    Cannot modify a read-only data structure
    """
    READ_ONLY: int = 22,

    """
    Incompatible format of the images
    """
    INCOMPATIBLE_IMAGE_FORMAT: int = 23,

    """
    Incompatible size of the images
    """
    INCOMPATIBLE_IMAGE_SIZE: int = 24,

    """
    Error while using a shared library (plugin)
    """
    SHARED_LIBRARY: int = 25,

    """
    Plugin invoking an unknown service
    """
    UNKNOWN_PLUGIN_SERVICE: int = 26,

    """
    Unknown DICOM tag
    """
    UNKNOWN_DICOM_TAG: int = 27,

    """
    Cannot parse a JSON document
    """
    BAD_JSON: int = 28,

    """
    Bad credentials were provided to an HTTP request
    """
    UNAUTHORIZED: int = 29,

    """
    Badly formatted font file
    """
    BAD_FONT: int = 30,

    """
    The plugin implementing a custom database back-end does not fulfill the proper interface
    """
    DATABASE_PLUGIN: int = 31,

    """
    Error in the plugin implementing a custom storage area
    """
    STORAGE_AREA_PLUGIN: int = 32,

    """
    The request is empty
    """
    EMPTY_REQUEST: int = 33,

    """
    Cannot send a response which is acceptable according to the Accept HTTP header
    """
    NOT_ACCEPTABLE: int = 34,

    """
    Cannot handle a NULL pointer
    """
    NULL_POINTER: int = 35,

    """
    The database is currently not available (probably a transient situation)
    """
    DATABASE_UNAVAILABLE: int = 36,

    """
    This job was canceled
    """
    CANCELED_JOB: int = 37,

    """
    Geometry error encountered in Stone
    """
    BAD_GEOMETRY: int = 38,

    """
    Cannot initialize SSL encryption, check out your certificates
    """
    SSL_INITIALIZATION: int = 39,

    """
    Calling a function that has been removed from the Orthanc Framework
    """
    DISCONTINUED_ABI: int = 40,

    """
    Incorrect range request
    """
    BAD_RANGE: int = 41,

    """
    Database could not serialize access due to concurrent update, the transaction should be retried
    """
    DATABASE_CANNOT_SERIALIZE: int = 42,

    """
    A bad revision number was provided, which might indicate conflict between multiple writers
    """
    REVISION: int = 43,

    """
    A main DICOM Tag has been defined multiple times for the same resource level
    """
    MAIN_DICOM_TAGS_MULTIPLY_DEFINED: int = 44,

    """
    Access to a resource is forbidden
    """
    FORBIDDEN_ACCESS: int = 45,

    """
    Duplicate resource
    """
    DUPLICATE_RESOURCE: int = 46,

    """
    Your configuration file contains configuration that are mutually incompatible
    """
    INCOMPATIBLE_CONFIGURATIONS: int = 47,

    """
    SQLite: The database is not opened
    """
    SQLITE_NOT_OPENED: int = 1000,

    """
    SQLite: Connection is already open
    """
    SQLITE_ALREADY_OPENED: int = 1001,

    """
    SQLite: Unable to open the database
    """
    SQLITE_CANNOT_OPEN: int = 1002,

    """
    SQLite: This cached statement is already being referred to
    """
    SQLITE_STATEMENT_ALREADY_USED: int = 1003,

    """
    SQLite: Cannot execute a command
    """
    SQLITE_EXECUTE: int = 1004,

    """
    SQLite: Rolling back a nonexistent transaction (have you called Begin()?)
    """
    SQLITE_ROLLBACK_WITHOUT_TRANSACTION: int = 1005,

    """
    SQLite: Committing a nonexistent transaction
    """
    SQLITE_COMMIT_WITHOUT_TRANSACTION: int = 1006,

    """
    SQLite: Unable to register a function
    """
    SQLITE_REGISTER_FUNCTION: int = 1007,

    """
    SQLite: Unable to flush the database
    """
    SQLITE_FLUSH: int = 1008,

    """
    SQLite: Cannot run a cached statement
    """
    SQLITE_CANNOT_RUN: int = 1009,

    """
    SQLite: Cannot step over a cached statement
    """
    SQLITE_CANNOT_STEP: int = 1010,

    """
    SQLite: Bind a value while out of range (serious error)
    """
    SQLITE_BIND_OUT_OF_RANGE: int = 1011,

    """
    SQLite: Cannot prepare a cached statement
    """
    SQLITE_PREPARE_STATEMENT: int = 1012,

    """
    SQLite: Beginning the same transaction twice
    """
    SQLITE_TRANSACTION_ALREADY_STARTED: int = 1013,

    """
    SQLite: Failure when committing the transaction
    """
    SQLITE_TRANSACTION_COMMIT: int = 1014,

    """
    SQLite: Cannot start a transaction
    """
    SQLITE_TRANSACTION_BEGIN: int = 1015,

    """
    The directory to be created is already occupied by a regular file
    """
    DIRECTORY_OVER_FILE: int = 2000,

    """
    Unable to create a subdirectory or a file in the file storage
    """
    FILE_STORAGE_CANNOT_WRITE: int = 2001,

    """
    The specified path does not point to a directory
    """
    DIRECTORY_EXPECTED: int = 2002,

    """
    The TCP port of the HTTP server is privileged or already in use or one of the HTTP bind addresses does not exist
    """
    HTTP_PORT_IN_USE: int = 2003,

    """
    The TCP port of the DICOM server is privileged or already in use
    """
    DICOM_PORT_IN_USE: int = 2004,

    """
    This HTTP status is not allowed in a REST API
    """
    BAD_HTTP_STATUS_IN_REST: int = 2005,

    """
    The specified path does not point to a regular file
    """
    REGULAR_FILE_EXPECTED: int = 2006,

    """
    Unable to get the path to the executable
    """
    PATH_TO_EXECUTABLE: int = 2007,

    """
    Cannot create a directory
    """
    MAKE_DIRECTORY: int = 2008,

    """
    An application entity title (AET) cannot be empty or be longer than 16 characters
    """
    BAD_APPLICATION_ENTITY_TITLE: int = 2009,

    """
    No request handler factory for DICOM C-FIND SCP
    """
    NO_CFIND_HANDLER: int = 2010,

    """
    No request handler factory for DICOM C-MOVE SCP
    """
    NO_CMOVE_HANDLER: int = 2011,

    """
    No request handler factory for DICOM C-STORE SCP
    """
    NO_CSTORE_HANDLER: int = 2012,

    """
    No application entity filter
    """
    NO_APPLICATION_ENTITY_FILTER: int = 2013,

    """
    DicomUserConnection: Unable to find the SOP class and instance
    """
    NO_SOP_CLASS_OR_INSTANCE: int = 2014,

    """
    DicomUserConnection: No acceptable presentation context for modality
    """
    NO_PRESENTATION_CONTEXT: int = 2015,

    """
    DicomUserConnection: The C-FIND command is not supported by the remote SCP
    """
    DICOM_FIND_UNAVAILABLE: int = 2016,

    """
    DicomUserConnection: The C-MOVE command is not supported by the remote SCP
    """
    DICOM_MOVE_UNAVAILABLE: int = 2017,

    """
    Cannot store an instance
    """
    CANNOT_STORE_INSTANCE: int = 2018,

    """
    Only string values are supported when creating DICOM instances
    """
    CREATE_DICOM_NOT_STRING: int = 2019,

    """
    Trying to override a value inherited from a parent module
    """
    CREATE_DICOM_OVERRIDE_TAG: int = 2020,

    """
    Use \"Content\" to inject an image into a new DICOM instance
    """
    CREATE_DICOM_USE_CONTENT: int = 2021,

    """
    No payload is present for one instance in the series
    """
    CREATE_DICOM_NO_PAYLOAD: int = 2022,

    """
    The payload of the DICOM instance must be specified according to Data URI scheme
    """
    CREATE_DICOM_USE_DATA_URI_SCHEME: int = 2023,

    """
    Trying to attach a new DICOM instance to an inexistent resource
    """
    CREATE_DICOM_BAD_PARENT: int = 2024,

    """
    Trying to attach a new DICOM instance to an instance (must be a series, study or patient)
    """
    CREATE_DICOM_PARENT_IS_INSTANCE: int = 2025,

    """
    Unable to get the encoding of the parent resource
    """
    CREATE_DICOM_PARENT_ENCODING: int = 2026,

    """
    Unknown modality
    """
    UNKNOWN_MODALITY: int = 2027,

    """
    Bad ordering of filters in a job
    """
    BAD_JOB_ORDERING: int = 2028,

    """
    Cannot convert the given JSON object to a Lua table
    """
    JSON_TO_LUA_TABLE: int = 2029,

    """
    Cannot create the Lua context
    """
    CANNOT_CREATE_LUA: int = 2030,

    """
    Cannot execute a Lua command
    """
    CANNOT_EXECUTE_LUA: int = 2031,

    """
    Arguments cannot be pushed after the Lua function is executed
    """
    LUA_ALREADY_EXECUTED: int = 2032,

    """
    The Lua function does not give the expected number of outputs
    """
    LUA_BAD_OUTPUT: int = 2033,

    """
    The Lua function is not a predicate (only true/false outputs allowed)
    """
    NOT_LUA_PREDICATE: int = 2034,

    """
    The Lua function does not return a string
    """
    LUA_RETURNS_NO_STRING: int = 2035,

    """
    Another plugin has already registered a custom storage area
    """
    STORAGE_AREA_ALREADY_REGISTERED: int = 2036,

    """
    Another plugin has already registered a custom database back-end
    """
    DATABASE_BACKEND_ALREADY_REGISTERED: int = 2037,

    """
    Plugin trying to call the database during its initialization
    """
    DATABASE_NOT_INITIALIZED: int = 2038,

    """
    Orthanc has been built without SSL support
    """
    SSL_DISABLED: int = 2039,

    """
    Unable to order the slices of the series
    """
    CANNOT_ORDER_SLICES: int = 2040,

    """
    No request handler factory for DICOM C-Find Modality SCP
    """
    NO_WORKLIST_HANDLER: int = 2041,

    """
    Cannot override the value of a tag that already exists
    """
    ALREADY_EXISTING_TAG: int = 2042,

    """
    No request handler factory for DICOM N-ACTION SCP (storage commitment)
    """
    NO_STORAGE_COMMITMENT_HANDLER: int = 2043,

    """
    No request handler factory for DICOM C-GET SCP
    """
    NO_CGET_HANDLER: int = 2044,

    """
    DicomUserConnection: The C-GET command is not supported by the remote SCP
    """
    DICOM_GET_UNAVAILABLE: int = 2045,

    """
    Unsupported media type
    """
    UNSUPPORTED_MEDIA_TYPE: int = 3000,

class HttpAuthenticationStatus():
    """
    Status associated with the authentication of a HTTP request.
    """

    """
    The authentication has been granted
    """
    GRANTED: int = 0,

    """
    The authentication has failed (401 HTTP status)
    """
    UNAUTHORIZED: int = 1,

    """
    The authorization has failed (403 HTTP status)
    """
    FORBIDDEN: int = 2,

    """
    Redirect to another path (307 HTTP status, e.g., for login)
    """
    REDIRECT: int = 3,

class HttpMethod():
    """
    The various HTTP methods for a REST call.
    """

    """
    GET request
    """
    GET: int = 1,

    """
    POST request
    """
    POST: int = 2,

    """
    PUT request
    """
    PUT: int = 3,

    """
    DELETE request
    """
    DELETE: int = 4,

class IdentifierConstraint():
    """
    The constraints on the DICOM identifiers that must be supported by the database plugins.
    """

    """
    Equal
    """
    EQUAL: int = 1,

    """
    Less or equal
    """
    SMALLER_OR_EQUAL: int = 2,

    """
    More or equal
    """
    GREATER_OR_EQUAL: int = 3,

    """
    Case-sensitive wildcard matching (with * and ?)
    """
    WILDCARD: int = 4,

class ImageFormat():
    """
    The image formats that are supported by the Orthanc core.
    """

    """
    Image compressed using PNG
    """
    PNG: int = 0,

    """
    Image compressed using JPEG
    """
    JPEG: int = 1,

    """
    Image compressed using DICOM
    """
    DICOM: int = 2,

class InstanceOrigin():
    """
    The origin of a DICOM instance that has been received by Orthanc.
    """

    """
    Unknown origin
    """
    UNKNOWN: int = 1,

    """
    Instance received through DICOM protocol
    """
    DICOM_PROTOCOL: int = 2,

    """
    Instance received through REST API of Orthanc
    """
    REST_API: int = 3,

    """
    Instance added to Orthanc by a plugin
    """
    PLUGIN: int = 4,

    """
    Instance added to Orthanc by a Lua script
    """
    LUA: int = 5,

    """
    Instance received through WebDAV (new in 1.8.0)
    """
    WEB_DAV: int = 6,

class JobStepStatus():
    """
    The possible status for one single step of a job.
    """

    """
    The job has successfully executed all its steps
    """
    SUCCESS: int = 1,

    """
    The job has failed while executing this step
    """
    FAILURE: int = 2,

    """
    The job has still data to process after this step
    """
    CONTINUE: int = 3,

class JobStopReason():
    """
    Explains why the job should stop and release the resources it has allocated. This is especially important to disambiguate between the "paused" condition and the "final" conditions (success, failure, or canceled).
    """

    """
    The job has succeeded
    """
    SUCCESS: int = 1,

    """
    The job was paused, and will be resumed later
    """
    PAUSED: int = 2,

    """
    The job has failed, and might be resubmitted later
    """
    FAILURE: int = 3,

    """
    The job was canceled, and might be resubmitted later
    """
    CANCELED: int = 4,

class LoadDicomInstanceMode():
    """
    Mode specifying how to load a DICOM instance.
    """

    """
    Load the whole DICOM file, including pixel data
    """
    WHOLE_DICOM: int = 1,

    """
    Load the whole DICOM file until pixel data, which speeds up the loading
    """
    UNTIL_PIXEL_DATA: int = 2,

    """
    Load the whole DICOM file until pixel data, and replace pixel data by an empty tag whose VR (value representation) is the same as those of the original DICOM file
    """
    EMPTY_PIXEL_DATA: int = 3,

class LogCategory():
    """
    The log categories supported by Orthanc. These values must match those of enumeration "LogCategory" in the Orthanc Core.
    """

    """
    Generic (default) category
    """
    GENERIC: int = 1,

    """
    Plugin engine related logs (shall not be used by plugins)
    """
    PLUGINS: int = 2,

    """
    HTTP related logs
    """
    HTTP: int = 4,

    """
    SQLite related logs (shall not be used by plugins)
    """
    SQLITE: int = 8,

    """
    DICOM related logs
    """
    DICOM: int = 16,

    """
    jobs related logs
    """
    JOBS: int = 32,

    """
    Lua related logs (shall not be used by plugins)
    """
    LUA: int = 64,

class LogLevel():
    """
    The log levels supported by Orthanc. These values must match those of enumeration "LogLevel" in the Orthanc Core.
    """

    """
    Error log level
    """
    ERROR: int = 0,

    """
    Warning log level
    """
    WARNING: int = 1,

    """
    Info log level
    """
    INFO: int = 2,

    """
    Trace log level
    """
    TRACE: int = 3,

class MetricsType():
    """
    The available types of metrics.
    """

    """
    Default metrics
    """
    DEFAULT: int = 0,

    """
    This metrics represents a time duration. Orthanc will keep the maximum value of the metrics over a sliding window of ten seconds, which is useful if the metrics is sampled frequently.
    """
    TIMER: int = 1,

class PixelFormat():
    """
    The memory layout of the pixels of an image.
    """

    """
    Graylevel 8bpp image. The image is graylevel. Each pixel is unsigned and stored in one byte.
    """
    GRAYSCALE8: int = 1,

    """
    Graylevel, unsigned 16bpp image. The image is graylevel. Each pixel is unsigned and stored in two bytes.
    """
    GRAYSCALE16: int = 2,

    """
    Graylevel, signed 16bpp image. The image is graylevel. Each pixel is signed and stored in two bytes.
    """
    SIGNED_GRAYSCALE16: int = 3,

    """
    Color image in RGB24 format. This format describes a color image. The pixels are stored in 3 consecutive bytes. The memory layout is RGB.
    """
    RGB24: int = 4,

    """
    Color image in RGBA32 format. This format describes a color image. The pixels are stored in 4 consecutive bytes. The memory layout is RGBA.
    """
    RGBA32: int = 5,

    """
    Unknown pixel format
    """
    UNKNOWN: int = 6,

    """
    Color image in RGB48 format. This format describes a color image. The pixels are stored in 6 consecutive bytes. The memory layout is RRGGBB.
    """
    RGB48: int = 7,

    """
    Graylevel, unsigned 32bpp image. The image is graylevel. Each pixel is unsigned and stored in four bytes.
    """
    GRAYSCALE32: int = 8,

    """
    Graylevel, floating-point 32bpp image. The image is graylevel. Each pixel is floating-point and stored in four bytes.
    """
    FLOAT32: int = 9,

    """
    Color image in BGRA32 format. This format describes a color image. The pixels are stored in 4 consecutive bytes. The memory layout is BGRA.
    """
    BGRA32: int = 10,

    """
    Graylevel, unsigned 64bpp image. The image is graylevel. Each pixel is unsigned and stored in eight bytes.
    """
    GRAYSCALE64: int = 11,

class QueueOrigin():
    """
    The supported modes to remove an element from a queue.
    """

    """
    Dequeue from the front of the queue
    """
    FRONT: int = 0,

    """
    Dequeue from the back of the queue
    """
    BACK: int = 1,

class ReceivedInstanceAction():
    """
    The action to be taken after ReceivedInstanceCallback is triggered
    """

    """
    Keep the instance as is
    """
    KEEP_AS_IS: int = 1,

    """
    Modify the instance
    """
    MODIFY: int = 2,

    """
    Discard the instance
    """
    DISCARD: int = 3,

class ResourceType():
    """
    The supported types of DICOM resources.
    """

    """
    Patient
    """
    PATIENT: int = 0,

    """
    Study
    """
    STUDY: int = 1,

    """
    Series
    """
    SERIES: int = 2,

    """
    Instance
    """
    INSTANCE: int = 3,

    """
    Unavailable resource type
    """
    NONE: int = 4,

class StableStatus():
    """
    The "Stable" status of a resource.
    """

    """
    The resource is stable
    """
    STABLE: int = 0,

    """
    The resource is unstable
    """
    UNSTABLE: int = 1,

class StorageCommitmentFailureReason():
    """
    The available values for the Failure Reason (0008,1197) during storage commitment. http://dicom.nema.org/medical/dicom/2019e/output/chtml/part03/sect_C.14.html#sect_C.14.1.1
    """

    """
    Success: The DICOM instance is properly stored in the SCP
    """
    SUCCESS: int = 0,

    """
    0110H: A general failure in processing the operation was encountered
    """
    PROCESSING_FAILURE: int = 1,

    """
    0112H: One or more of the elements in the Referenced SOP Instance Sequence was not available
    """
    NO_SUCH_OBJECT_INSTANCE: int = 2,

    """
    0213H: The SCP does not currently have enough resources to store the requested SOP Instance(s)
    """
    RESOURCE_LIMITATION: int = 3,

    """
    0122H: Storage Commitment has been requested for a SOP Instance with a SOP Class that is not supported by the SCP
    """
    REFERENCED_SOPCLASS_NOT_SUPPORTED: int = 4,

    """
    0119H: The SOP Class of an element in the Referenced SOP Instance Sequence did not correspond to the SOP class registered for this SOP Instance at the SCP
    """
    CLASS_INSTANCE_CONFLICT: int = 5,

    """
    0131H: The Transaction UID of the Storage Commitment Request is already in use
    """
    DUPLICATE_TRANSACTION_UID: int = 6,

class StoreStatus():
    """
    The store status related to the adoption of a DICOM instance.
    """

    """
    The file has been stored/adopted
    """
    SUCCESS: int = 0,

    """
    The file has already been stored/adopted (only if OverwriteInstances is set to false)
    """
    ALREADY_STORED: int = 1,

    """
    The file could not be stored/adopted
    """
    FAILURE: int = 2,

    """
    The file has been filtered out by a Lua script or a plugin
    """
    FILTERED_OUT: int = 3,

    """
    The storage is full (only if MaximumStorageSize/MaximumPatientCount is set and MaximumStorageMode is Reject)
    """
    STORAGE_FULL: int = 4,

class ValueRepresentation():
    """
    The value representations present in the DICOM standard (version 2013).
    """

    """
    Application Entity
    """
    AE: int = 1,

    """
    Age String
    """
    AS: int = 2,

    """
    Attribute Tag
    """
    AT: int = 3,

    """
    Code String
    """
    CS: int = 4,

    """
    Date
    """
    DA: int = 5,

    """
    Decimal String
    """
    DS: int = 6,

    """
    Date Time
    """
    DT: int = 7,

    """
    Floating Point Double
    """
    FD: int = 8,

    """
    Floating Point Single
    """
    FL: int = 9,

    """
    Integer String
    """
    IS: int = 10,

    """
    Long String
    """
    LO: int = 11,

    """
    Long Text
    """
    LT: int = 12,

    """
    Other Byte String
    """
    OB: int = 13,

    """
    Other Float String
    """
    OF: int = 14,

    """
    Other Word String
    """
    OW: int = 15,

    """
    Person Name
    """
    PN: int = 16,

    """
    Short String
    """
    SH: int = 17,

    """
    Signed Long
    """
    SL: int = 18,

    """
    Sequence of Items
    """
    SQ: int = 19,

    """
    Signed Short
    """
    SS: int = 20,

    """
    Short Text
    """
    ST: int = 21,

    """
    Time
    """
    TM: int = 22,

    """
    Unique Identifier (UID)
    """
    UI: int = 23,

    """
    Unsigned Long
    """
    UL: int = 24,

    """
    Unknown
    """
    UN: int = 25,

    """
    Unsigned Short
    """
    US: int = 26,

    """
    Unlimited Text
    """
    UT: int = 27,



def AcknowledgeQueueValue(queue_id: str, value_id: int) -> None:
    """

    Args:
      queue_id (str): A unique identifier identifying both the plugin and the queue.
      value_id (int): The opaque identifier for the value provided by OrthancPluginReserveQueueValue().
    """
    ...

# This function returns the MIME type of a file by inspecting its extension
def AutodetectMimeType(path: str) -> str:
    """
    This function returns the MIME type of a file by inspecting its extension.

    Args:
      path (str): Path to the file.

    Returns:
      str: The MIME type. This is a statically-allocated string, do not free it.
    """
    ...

# This function compresses or decompresses a buffer, using the version of the zlib library that is used by the Orthanc core
def BufferCompression(source: bytes, compression: CompressionType, uncompress: int) -> bytes:
    """
    This function compresses or decompresses a buffer, using the version of the zlib library that is used by the Orthanc core.

    Args:
      source (bytes): The source buffer.
      compression (CompressionType): The compression algorithm.
      uncompress (int): If set to "0", the buffer must be compressed. If set to "1", the buffer must be uncompressed.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# This function checks whether the version of the Orthanc server running this plugin, is above the version of the current Orthanc SDK header
def CheckVersion() -> int:
    """
    This function checks whether the version of the Orthanc server running this plugin, is above the version of the current Orthanc SDK header. This guarantees that the plugin is compatible with the hosting Orthanc (i.e. it will not call unavailable services). The result of this function should always be checked in the OrthancPluginInitialize() entry point of the plugin.

    Returns:
      int: 1 if and only if the versions are compatible. If the result is 0, the initialization of the plugin should fail.
    """
    ...

# This function checks whether the version of the Orthanc server running this plugin, is above the given version
def CheckVersionAdvanced(expected_major: int, expected_minor: int, expected_revision: int) -> int:
    """
    This function checks whether the version of the Orthanc server running this plugin, is above the given version. Contrarily to OrthancPluginCheckVersion(), it is up to the developer of the plugin to make sure that all the Orthanc SDK services called by the plugin are actually implemented in the given version of Orthanc.

    Args:
      expected_major (int): Expected major version.
      expected_minor (int): Expected minor version.
      expected_revision (int): Expected revision.

    Returns:
      int: 1 if and only if the versions are compatible. If the result is 0, the initialization of the plugin should fail.
    """
    ...

# This function compresses the given memory buffer containing an image using the JPEG specification, and stores the result of the compression into a newly allocated memory buffer
def CompressJpegImage(format: PixelFormat, width: int, height: int, pitch: int, buffer: bytes, quality: int) -> bytes:
    """
    This function compresses the given memory buffer containing an image using the JPEG specification, and stores the result of the compression into a newly allocated memory buffer.

    Args:
      format (PixelFormat): The memory layout of the uncompressed image.
      width (int): The width of the image.
      height (int): The height of the image.
      pitch (int): The pitch of the image (i.e. the number of bytes between 2 successive lines of the image in the memory buffer).
      buffer (bytes): The memory buffer containing the uncompressed image.
      quality (int): The quality of the JPEG encoding, between 1 (worst quality, best compression) and 100 (best quality, worst compression).

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# This function compresses the given memory buffer containing an image using the PNG specification, and stores the result of the compression into a newly allocated memory buffer
def CompressPngImage(format: PixelFormat, width: int, height: int, pitch: int, buffer: bytes) -> bytes:
    """
    This function compresses the given memory buffer containing an image using the PNG specification, and stores the result of the compression into a newly allocated memory buffer.

    Args:
      format (PixelFormat): The memory layout of the uncompressed image.
      width (int): The width of the image.
      height (int): The height of the image.
      pitch (int): The pitch of the image (i.e. the number of bytes between 2 successive lines of the image in the memory buffer).
      buffer (bytes): The memory buffer containing the uncompressed image.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# This functions computes the MD5 cryptographic hash of the given memory buffer
def ComputeMd5(buffer: bytes) -> str:
    """
    This functions computes the MD5 cryptographic hash of the given memory buffer.

    Args:
      buffer (bytes): The source memory buffer.

    Returns:
      str: The NULL value in case of error, or a string containing the cryptographic hash. This string must be freed by OrthancPluginFreeString().
    """
    ...

# This functions computes the SHA-1 cryptographic hash of the given memory buffer
def ComputeSha1(buffer: bytes) -> str:
    """
    This functions computes the SHA-1 cryptographic hash of the given memory buffer.

    Args:
      buffer (bytes): The source memory buffer.

    Returns:
      str: The NULL value in case of error, or a string containing the cryptographic hash. This string must be freed by OrthancPluginFreeString().
    """
    ...

# This function takes as input a string containing a JSON file describing the content of a DICOM instance
def CreateDicom(json: str, pixel_data: Image, flags: CreateDicomFlags) -> bytes:
    """
    This function takes as input a string containing a JSON file describing the content of a DICOM instance. As an output, it writes the corresponding DICOM instance to a newly allocated memory buffer. Additionally, an image to be encoded within the DICOM instance can also be provided.
    Private tags will be associated with the private creator whose value is specified in the "DefaultPrivateCreator" configuration option of Orthanc. The function OrthancPluginCreateDicom2() can be used if another private creator must be used to create this instance.

    Args:
      json (str): The input JSON file.
      pixel_data (Image): The image. Can be NULL, if the pixel data is encoded inside the JSON with the data URI scheme.
      flags (CreateDicomFlags): Flags governing the output.

    Returns:
      bytes: 0 if success, other value if error.
    """
    ...

# This function takes as input a string containing a JSON file describing the content of a DICOM instance
def CreateDicom2(json: str, pixel_data: Image, flags: CreateDicomFlags, private_creator: str) -> bytes:
    """
    This function takes as input a string containing a JSON file describing the content of a DICOM instance. As an output, it writes the corresponding DICOM instance to a newly allocated memory buffer. Additionally, an image to be encoded within the DICOM instance can also be provided.
    Contrarily to the function OrthancPluginCreateDicom(), this function can be explicitly provided with a private creator.

    Args:
      json (str): The input JSON file.
      pixel_data (Image): The image. Can be NULL, if the pixel data is encoded inside the JSON with the data URI scheme.
      flags (CreateDicomFlags): Flags governing the output.
      private_creator (str): The private creator to be used for the private DICOM tags. Check out the global configuration option "Dictionary" of Orthanc.

    Returns:
      bytes: 0 if success, other value if error.
    """
    ...

# This function parses a memory buffer that contains a DICOM file
def CreateDicomInstance(buffer: bytes) -> DicomInstance:
    """
    This function parses a memory buffer that contains a DICOM file. The function returns a new pointer to a data structure that is managed by the Orthanc core.

    Args:
      buffer (bytes): The memory buffer containing the DICOM instance.

    Returns:
      DicomInstance: The newly allocated DICOM instance. It must be freed with OrthancPluginFreeDicomInstance().
    """
    ...

# This function creates a "matcher" object that can be used to check whether a DICOM instance matches a C-Find query
def CreateFindMatcher(query: bytes) -> FindMatcher:
    """
    This function creates a "matcher" object that can be used to check whether a DICOM instance matches a C-Find query. The C-Find query must be expressed as a DICOM buffer.

    Args:
      query (bytes): The C-Find DICOM query.

    Returns:
      FindMatcher: The newly allocated matcher. It must be freed with OrthancPluginFreeFindMatcher().
    """
    ...

# This function creates an image of given size and format
def CreateImage(format: PixelFormat, width: int, height: int) -> Image:
    """
    This function creates an image of given size and format.

    Args:
      format (PixelFormat): The format of the pixels.
      width (int): The width of the image.
      height (int): The height of the image.

    Returns:
      Image: The newly allocated image. It must be freed with OrthancPluginFreeImage().
    """
    ...

# The iterator loops over the keys according to the lexicographical order
def CreateKeysValuesIterator(store_id: str) -> KeysValuesIterator:
    """
    The iterator loops over the keys according to the lexicographical order.

    Args:
      store_id (str): A unique identifier identifying both the plugin and the key-value store.

    Returns:
      KeysValuesIterator: The newly allocated iterator, or NULL in the case of an error. The iterator must be freed by calling OrthancPluginFreeKeysValuesIterator().
    """
    ...

# This function decodes one frame of a DICOM image that is stored in a memory buffer
def DecodeDicomImage(buffer: bytes, frame_index: int) -> Image:
    """
    This function decodes one frame of a DICOM image that is stored in a memory buffer. This function will give the same result as OrthancPluginUncompressImage() for single-frame DICOM images.

    Args:
      buffer (bytes): Pointer to a memory buffer containing the DICOM image.
      frame_index (int): The index of the frame of interest in a multi-frame image.

    Returns:
      Image: The uncompressed image. It must be freed with OrthancPluginFreeImage().
    """
    ...

def DeleteKeyValue(store_id: str, key: str) -> None:
    """

    Args:
      store_id (str): A unique identifier identifying both the plugin and the key-value store.
      key (str): The key of the value to store (note: storeId + key must be unique).
    """
    ...

# This function takes as input a memory buffer containing a DICOM file, and outputs a JSON string representing the tags of this DICOM file
def DicomBufferToJson(buffer: bytes, format: DicomToJsonFormat, flags: DicomToJsonFlags, max_string_length: int) -> str:
    """
    This function takes as input a memory buffer containing a DICOM file, and outputs a JSON string representing the tags of this DICOM file.

    Args:
      buffer (bytes): The memory buffer containing the DICOM file.
      format (DicomToJsonFormat): The output format.
      flags (DicomToJsonFlags): Flags governing the output.
      max_string_length (int): The maximum length of a field. Too long fields will be output as "null". The 0 value means no maximum length.

    Returns:
      str: The NULL value if the case of an error, or the JSON string. This string must be freed by OrthancPluginFreeString().
    """
    ...

# This function formats a DICOM instance that is stored in Orthanc, and outputs a JSON string representing the tags of this DICOM instance
def DicomInstanceToJson(instance_id: str, format: DicomToJsonFormat, flags: DicomToJsonFlags, max_string_length: int) -> str:
    """
    This function formats a DICOM instance that is stored in Orthanc, and outputs a JSON string representing the tags of this DICOM instance.

    Args:
      instance_id (str): The Orthanc identifier of the instance.
      format (DicomToJsonFormat): The output format.
      flags (DicomToJsonFlags): Flags governing the output.
      max_string_length (int): The maximum length of a field. Too long fields will be output as "null". The 0 value means no maximum length.

    Returns:
      str: The NULL value if the case of an error, or the JSON string. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Generate an audit log that will be broadcasted to all the plugins that have registered a callback handler using OrthancPluginRegisterAuditLogHandler()
def EmitAuditLog(source_plugin: str, user_id: str, resource_type: ResourceType, resource_id: str, action: str, log_data: bytes) -> None:
    """
    Generate an audit log that will be broadcasted to all the plugins that have registered a callback handler using OrthancPluginRegisterAuditLogHandler(). If no plugin has registered such a callback, the audit log is ignored.
    A typical handler would record the audit log in a database and/or relay the audit log to a message broker.

    Args:
      source_plugin (str): The name of the source plugin, to properly interpret the content of "action" and "logData".
      user_id (str): A string that uniquely identifies the user or entity that is executing the action on the resource.
      resource_type (ResourceType): The type of the resource this audit log relates to.
      resource_id (str): The resource this audit log relates to.
      action (str): The action that was performed on the resource.
      log_data (bytes): A pointer to custom log data.
    """
    ...

def EnqueueValue(queue_id: str, value: bytes) -> None:
    """

    Args:
      queue_id (str): A unique identifier identifying both the plugin and the queue.
      value (bytes): The value to store.
    """
    ...

# Add JavaScript code to customize the default behavior of Orthanc Explorer
def ExtendOrthancExplorer(javascript: str) -> None:
    """
    Add JavaScript code to customize the default behavior of Orthanc Explorer. This can for instance be used to add new buttons.

    Args:
      javascript (str): The custom JavaScript code.
    """
    ...

# Add JavaScript code to customize the default behavior of Orthanc Explorer
def ExtendOrthancExplorer2(plugin: str, javascript: str) -> None:
    """
    Add JavaScript code to customize the default behavior of Orthanc Explorer. This can for instance be used to add new buttons.

    Args:
      plugin (str): Identifier of your plugin (it must match "OrthancPluginGetName()").
      javascript (str): The custom JavaScript code.
    """
    ...

# This function generates a token that can be set in the HTTP header "Authorization" so as to grant full access to the REST API of Orthanc using an external HTTP client
def GenerateRestApiAuthorizationToken() -> str:
    """
    This function generates a token that can be set in the HTTP header "Authorization" so as to grant full access to the REST API of Orthanc using an external HTTP client. Using this function avoids the need of adding a separate user in the "RegisteredUsers" configuration of Orthanc, which eases deployments.
    This feature is notably useful in multiprocess scenarios, where a subprocess created by a plugin has no access to the "OrthancPluginContext", and thus cannot call "OrthancPluginRestApi[Get|Post|Put|Delete]()".
    This situation is frequently encountered in Python plugins, where the "multiprocessing" package can be used to bypass the Global Interpreter Lock (GIL) and thus to improve performance and concurrency.

    Returns:
      str: The authorization token, or NULL value in the case of an error. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Generate a random GUID/UUID (globally unique identifier)
def GenerateUuid() -> str:
    """
    Generate a random GUID/UUID (globally unique identifier).

    Returns:
      str: NULL in the case of an error, or a newly allocated string containing the UUID. This string must be freed by OrthancPluginFreeString().
    """
    ...

# If no custom data is associated with the attachment of interest, the target memory buffer is filled with the NULL value and a zero size
def GetAttachmentCustomData(attachment_uuid: str) -> bytes:
    """
    If no custom data is associated with the attachment of interest, the target memory buffer is filled with the NULL value and a zero size.

    Args:
      attachment_uuid (str): The UUID of the attachment of interest.

    Returns:
      bytes: 0 if success, other value if error.
    """
    ...

# Get the value of one of the command-line arguments that were used to launch Orthanc
def GetCommandLineArgument(argument: int) -> str:
    """
    Get the value of one of the command-line arguments that were used to launch Orthanc. The number of available arguments can be retrieved by OrthancPluginGetCommandLineArgumentsCount().

    Args:
      argument (int): The index of the argument.

    Returns:
      str: The value of the argument, or NULL in the case of an error. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Retrieve the number of command-line arguments that were used to launch Orthanc
def GetCommandLineArgumentsCount() -> int:
    """
    Retrieve the number of command-line arguments that were used to launch Orthanc.

    Returns:
      int: The number of arguments.
    """
    ...

# This function returns the content of the configuration that is used by Orthanc, formatted as a JSON string
def GetConfiguration() -> str:
    """
    This function returns the content of the configuration that is used by Orthanc, formatted as a JSON string.

    Returns:
      str: NULL in the case of an error, or a newly allocated string containing the configuration. This string must be freed by OrthancPluginFreeString().
    """
    ...

# This function returns the path to the configuration file(s) that was specified when starting Orthanc
def GetConfigurationPath() -> str:
    """
    This function returns the path to the configuration file(s) that was specified when starting Orthanc. Since version 0.9.1, this path can refer to a folder that stores a set of configuration files. This function is deprecated in favor of OrthancPluginGetConfiguration().

    Returns:
      str: NULL in the case of an error, or a newly allocated string containing the path. This string must be freed by OrthancPluginFreeString().
    """
    ...

def GetDatabaseServerIdentifier() -> str:
    """

    Returns:
      str: the database server identifier.  This is a statically-allocated string, do not free it.
    """
    ...

# Retrieve a DICOM instance using its Orthanc identifier
def GetDicomForInstance(instance_id: str) -> bytes:
    """
    Retrieve a DICOM instance using its Orthanc identifier. The DICOM file is stored into a newly allocated memory buffer.

    Args:
      instance_id (str): The Orthanc identifier of the DICOM instance of interest.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# This function returns the description of a given error code
def GetErrorDescription(error: ErrorCode) -> str:
    """
    This function returns the description of a given error code.

    Args:
      error (ErrorCode): The error code of interest.

    Returns:
      str: The error description. This is a statically-allocated string, do not free it.
    """
    ...

# Retrieve the expected version of the database schema
def GetExpectedDatabaseVersion() -> int:
    """
    Retrieve the expected version of the database schema.

    Returns:
      int: The version.
    """
    ...

# This function returns the name of a font that is built in the Orthanc core
def GetFontName(font_index: int) -> str:
    """
    This function returns the name of a font that is built in the Orthanc core.

    Args:
      font_index (int): The index of the font. This value must be less than OrthancPluginGetFontsCount().

    Returns:
      str: The font name. This is a statically-allocated string, do not free it.
    """
    ...

# This function returns the size of a font that is built in the Orthanc core
def GetFontSize(font_index: int) -> int:
    """
    This function returns the size of a font that is built in the Orthanc core.

    Args:
      font_index (int): The index of the font. This value must be less than OrthancPluginGetFontsCount().

    Returns:
      int: The font size.
    """
    ...

# This function returns the number of fonts that are built in the Orthanc core
def GetFontsCount() -> int:
    """
    This function returns the number of fonts that are built in the Orthanc core. These fonts can be used to draw texts on images through OrthancPluginDrawText().

    Returns:
      int: The number of fonts.
    """
    ...

# Get the value of a global property that is stored in the Orthanc database
def GetGlobalProperty(property: int, default_value: str) -> str:
    """
    Get the value of a global property that is stored in the Orthanc database. Global properties whose index is below 1024 are reserved by Orthanc.

    Args:
      property (int): The global property of interest.
      default_value (str): The value to return, if the global property is unset.

    Returns:
      str: The value of the global property, or NULL in the case of an error. This string must be freed by OrthancPluginFreeString().
    """
    ...

# This function returns the path to the directory containing the Orthanc executable
def GetOrthancDirectory() -> str:
    """
    This function returns the path to the directory containing the Orthanc executable.

    Returns:
      str: NULL in the case of an error, or a newly allocated string containing the path. This string must be freed by OrthancPluginFreeString().
    """
    ...

# This function returns the path to the Orthanc executable
def GetOrthancPath() -> str:
    """
    This function returns the path to the Orthanc executable.

    Returns:
      str: NULL in the case of an error, or a newly allocated string containing the path. This string must be freed by OrthancPluginFreeString().
    """
    ...

# This function returns the parameters of the Orthanc peers that are known to the Orthanc server hosting the plugin
def GetPeers() -> Peers:
    """
    This function returns the parameters of the Orthanc peers that are known to the Orthanc server hosting the plugin.

    Returns:
      Peers: NULL if error, or a newly allocated opaque data structure containing the peers. This structure must be freed with OrthancPluginFreePeers().
    """
    ...

# This function makes a lookup to the dictionary of DICOM tags that are known to Orthanc, and returns the symbolic name of a DICOM tag
def GetTagName(group: int, element: int, private_creator: str) -> str:
    """
    This function makes a lookup to the dictionary of DICOM tags that are known to Orthanc, and returns the symbolic name of a DICOM tag.

    Args:
      group (int): The group of the tag.
      element (int): The element of the tag.
      private_creator (str): For private tags, the name of the private creator (can be NULL).

    Returns:
      str: NULL in the case of an error, or a newly allocated string containing the path. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Make a HTTP DELETE call to the given URL
def HttpDelete(url: str, username: str, password: str) -> None:
    """
    Make a HTTP DELETE call to the given URL. Favor OrthancPluginRestApiDelete() if calling the built-in REST API of the Orthanc instance that hosts this plugin.

    Args:
      url (str): The URL of interest.
      username (str): The username (can be "NULL" if no password protection).
      password (str): The password (can be "NULL" if no password protection).
    """
    ...

# Make a HTTP GET call to the given URL
def HttpGet(url: str, username: str, password: str) -> bytes:
    """
    Make a HTTP GET call to the given URL. The result to the query is stored into a newly allocated memory buffer. Favor OrthancPluginRestApiGet() if calling the built-in REST API of the Orthanc instance that hosts this plugin.

    Args:
      url (str): The URL of interest.
      username (str): The username (can be "NULL" if no password protection).
      password (str): The password (can be "NULL" if no password protection).

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# Make a HTTP POST call to the given URL
def HttpPost(url: str, body: bytes, username: str, password: str) -> bytes:
    """
    Make a HTTP POST call to the given URL. The result to the query is stored into a newly allocated memory buffer. Favor OrthancPluginRestApiPost() if calling the built-in REST API of the Orthanc instance that hosts this plugin.

    Args:
      url (str): The URL of interest.
      body (bytes): The content of the body of the request.
      username (str): The username (can be "NULL" if no password protection).
      password (str): The password (can be "NULL" if no password protection).

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# Make a HTTP PUT call to the given URL
def HttpPut(url: str, body: bytes, username: str, password: str) -> bytes:
    """
    Make a HTTP PUT call to the given URL. The result to the query is stored into a newly allocated memory buffer. Favor OrthancPluginRestApiPut() if calling the built-in REST API of the Orthanc instance that hosts this plugin.

    Args:
      url (str): The URL of interest.
      body (bytes): The content of the body of the request.
      username (str): The username (can be "NULL" if no password protection).
      password (str): The password (can be "NULL" if no password protection).

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# This function loads a DICOM instance from the content of the Orthanc database
def LoadDicomInstance(instance_id: str, mode: LoadDicomInstanceMode) -> DicomInstance:
    """
    This function loads a DICOM instance from the content of the Orthanc database. The function returns a new pointer to a data structure that is managed by the Orthanc core.

    Args:
      instance_id (str): The Orthanc identifier of the DICOM instance of interest.
      mode (LoadDicomInstanceMode): Flag specifying how to deal with pixel data.

    Returns:
      DicomInstance: The newly allocated DICOM instance. It must be freed with OrthancPluginFreeDicomInstance().
    """
    ...

# Log an error message using the Orthanc logging system
def LogError(message: str) -> None:
    """
    Log an error message using the Orthanc logging system.

    Args:
      message (str): The message to be logged.
    """
    ...

# Log an information message using the Orthanc logging system
def LogInfo(message: str) -> None:
    """
    Log an information message using the Orthanc logging system.

    Args:
      message (str): The message to be logged.
    """
    ...

# Log a message using the Orthanc logging system
def LogMessage(message: str, plugin: str, file: str, line: int, category: LogCategory, level: LogLevel) -> None:
    """
    Log a message using the Orthanc logging system.

    Args:
      message (str): The message to be logged.
      plugin (str): The plugin name.
      file (str): The filename in the plugin code.
      line (int): The file line in the plugin code.
      category (LogCategory): The category.
      level (LogLevel): The level of the message.
    """
    ...

# Log a warning message using the Orthanc logging system
def LogWarning(message: str) -> None:
    """
    Log a warning message using the Orthanc logging system.

    Args:
      message (str): The message to be logged.
    """
    ...

# Look for an instance stored in Orthanc, using its SOP Instance UID tag (0x0008, 0x0018)
def LookupInstance(sop_instance_u_i_d: str) -> str:
    """
    Look for an instance stored in Orthanc, using its SOP Instance UID tag (0x0008, 0x0018). This function uses the database index to run as fast as possible (it does not loop over all the stored instances).

    Args:
      sop_instance_u_i_d (str): The SOP Instance UID of interest.

    Returns:
      str: The NULL value if the instance is non-existent, or a string containing the Orthanc ID of the instance. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Look for a patient stored in Orthanc, using its Patient ID tag (0x0010, 0x0020)
def LookupPatient(patient_i_d: str) -> str:
    """
    Look for a patient stored in Orthanc, using its Patient ID tag (0x0010, 0x0020). This function uses the database index to run as fast as possible (it does not loop over all the stored patients).

    Args:
      patient_i_d (str): The Patient ID of interest.

    Returns:
      str: The NULL value if the patient is non-existent, or a string containing the Orthanc ID of the patient. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Look for a series stored in Orthanc, using its Series Instance UID tag (0x0020, 0x000e)
def LookupSeries(series_u_i_d: str) -> str:
    """
    Look for a series stored in Orthanc, using its Series Instance UID tag (0x0020, 0x000e). This function uses the database index to run as fast as possible (it does not loop over all the stored series).

    Args:
      series_u_i_d (str): The Series Instance UID of interest.

    Returns:
      str: The NULL value if the series is non-existent, or a string containing the Orthanc ID of the series. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Look for a study stored in Orthanc, using its Study Instance UID tag (0x0020, 0x000d)
def LookupStudy(study_u_i_d: str) -> str:
    """
    Look for a study stored in Orthanc, using its Study Instance UID tag (0x0020, 0x000d). This function uses the database index to run as fast as possible (it does not loop over all the stored studies).

    Args:
      study_u_i_d (str): The Study Instance UID of interest.

    Returns:
      str: The NULL value if the study is non-existent, or a string containing the Orthanc ID of the study. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Look for a study stored in Orthanc, using its Accession Number tag (0x0008, 0x0050)
def LookupStudyWithAccessionNumber(accession_number: str) -> str:
    """
    Look for a study stored in Orthanc, using its Accession Number tag (0x0008, 0x0050). This function uses the database index to run as fast as possible (it does not loop over all the stored studies).

    Args:
      accession_number (str): The Accession Number of interest.

    Returns:
      str: The NULL value if the study is non-existent, or a string containing the Orthanc ID of the study. This string must be freed by OrthancPluginFreeString().
    """
    ...

# Read the content of a file on the filesystem, and returns it into a newly allocated memory buffer
def ReadFile(path: str) -> bytes:
    """
    Read the content of a file on the filesystem, and returns it into a newly allocated memory buffer.

    Args:
      path (str): The path of the file to be read.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# This function declares a new public tag in the dictionary of DICOM tags that are known to Orthanc
def RegisterDictionaryTag(group: int, element: int, vr: ValueRepresentation, name: str, min_multiplicity: int, max_multiplicity: int) -> None:
    """
    This function declares a new public tag in the dictionary of DICOM tags that are known to Orthanc. This function should be used in the OrthancPluginInitialize() callback.

    Args:
      group (int): The group of the tag.
      element (int): The element of the tag.
      vr (ValueRepresentation): The value representation of the tag.
      name (str): The nickname of the tag.
      min_multiplicity (int): The minimum multiplicity of the tag (must be above 0).
      max_multiplicity (int): The maximum multiplicity of the tag. A value of 0 means an arbitrary multiplicity (""n"").
    """
    ...

# This function declares a custom error code that can be generated by this plugin
def RegisterErrorCode(code: int, http_status: int, message: str) -> None:
    """
    This function declares a custom error code that can be generated by this plugin. This declaration is used to enrich the body of the HTTP answer in the case of an error, and to set the proper HTTP status code.

    Args:
      code (int): The error code that is internal to this plugin.
      http_status (int): The HTTP status corresponding to this error.
      message (str): The description of the error.
    """
    ...

# This function declares a new private tag in the dictionary of DICOM tags that are known to Orthanc
def RegisterPrivateDictionaryTag(group: int, element: int, vr: ValueRepresentation, name: str, min_multiplicity: int, max_multiplicity: int, private_creator: str) -> None:
    """
    This function declares a new private tag in the dictionary of DICOM tags that are known to Orthanc. This function should be used in the OrthancPluginInitialize() callback.

    Args:
      group (int): The group of the tag.
      element (int): The element of the tag.
      vr (ValueRepresentation): The value representation of the tag.
      name (str): The nickname of the tag.
      min_multiplicity (int): The minimum multiplicity of the tag (must be above 0).
      max_multiplicity (int): The maximum multiplicity of the tag. A value of 0 means an arbitrary multiplicity (""n"").
      private_creator (str): The private creator of this private tag.
    """
    ...

# Make a DELETE call to the built-in Orthanc REST API
def RestApiDelete(uri: str) -> None:
    """
    Make a DELETE call to the built-in Orthanc REST API.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI to delete in the built-in Orthanc API.
    """
    ...

# Make a DELETE call to the Orthanc REST API, after all the plugins are applied
def RestApiDeleteAfterPlugins(uri: str) -> None:
    """
    Make a DELETE call to the Orthanc REST API, after all the plugins are applied. In other words, if some plugin overrides or adds the called URI to the built-in Orthanc REST API, this call will return the result provided by this plugin.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI to delete in the built-in Orthanc API.
    """
    ...

# Make a GET call to the built-in Orthanc REST API
def RestApiGet(uri: str) -> bytes:
    """
    Make a GET call to the built-in Orthanc REST API. The result to the query is stored into a newly allocated memory buffer.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI in the built-in Orthanc API.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# Make a GET call to the Orthanc REST API, after all the plugins are applied
def RestApiGetAfterPlugins(uri: str) -> bytes:
    """
    Make a GET call to the Orthanc REST API, after all the plugins are applied. In other words, if some plugin overrides or adds the called URI to the built-in Orthanc REST API, this call will return the result provided by this plugin. The result to the query is stored into a newly allocated memory buffer.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI in the built-in Orthanc API.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# Make a POST call to the built-in Orthanc REST API
def RestApiPost(uri: str, body: bytes) -> bytes:
    """
    Make a POST call to the built-in Orthanc REST API. The result to the query is stored into a newly allocated memory buffer.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI in the built-in Orthanc API.
      body (bytes): The body of the POST request.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# Make a POST call to the Orthanc REST API, after all the plugins are applied
def RestApiPostAfterPlugins(uri: str, body: bytes) -> bytes:
    """
    Make a POST call to the Orthanc REST API, after all the plugins are applied. In other words, if some plugin overrides or adds the called URI to the built-in Orthanc REST API, this call will return the result provided by this plugin. The result to the query is stored into a newly allocated memory buffer.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI in the built-in Orthanc API.
      body (bytes): The body of the POST request.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# Make a PUT call to the built-in Orthanc REST API
def RestApiPut(uri: str, body: bytes) -> bytes:
    """
    Make a PUT call to the built-in Orthanc REST API. The result to the query is stored into a newly allocated memory buffer.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI in the built-in Orthanc API.
      body (bytes): The body of the PUT request.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# Make a PUT call to the Orthanc REST API, after all the plugins are applied
def RestApiPutAfterPlugins(uri: str, body: bytes) -> bytes:
    """
    Make a PUT call to the Orthanc REST API, after all the plugins are applied. In other words, if some plugin overrides or adds the called URI to the built-in Orthanc REST API, this call will return the result provided by this plugin. The result to the query is stored into a newly allocated memory buffer.
    Remark: If the resource is not existing (error 404), the error code will be OrthancPluginErrorCode_UnknownResource.

    Args:
      uri (str): The URI in the built-in Orthanc API.
      body (bytes): The body of the PUT request.

    Returns:
      bytes: 0 if success, or the error code if failure.
    """
    ...

# This function is notably used in the "orthanc-advanced-storage" when the plugin moves an attachment
def SetAttachmentCustomData(attachment_uuid: str, custom_data: bytes) -> None:
    """
    This function is notably used in the "orthanc-advanced-storage" when the plugin moves an attachment.

    Args:
      attachment_uuid (str): The UUID of the attachment of interest.
      custom_data (bytes): The value to store.
    """
    ...

# This function gives a name to the thread that is calling this function
def SetCurrentThreadName(thread_name: str) -> None:
    """
    This function gives a name to the thread that is calling this function. This name is used in the Orthanc logs. This function must only be called from threads that the plugin has created itself.

    Args:
      thread_name (str): The name of the current thread. A thread name cannot be longer than 16 characters.
    """
    ...

# Set a description for this plugin
def SetDescription(description: str) -> None:
    """
    Set a description for this plugin. It is displayed in the "Plugins" page of Orthanc Explorer.

    Args:
      description (str): The description.
    """
    ...

# Set a description for this plugin
def SetDescription2(plugin: str, description: str) -> None:
    """
    Set a description for this plugin. It is displayed in the "Plugins" page of Orthanc Explorer.

    Args:
      plugin (str): Identifier of your plugin (it must match "OrthancPluginGetName()").
      description (str): The description.
    """
    ...

# Set the value of a global property into the Orthanc database
def SetGlobalProperty(property: int, value: str) -> None:
    """
    Set the value of a global property into the Orthanc database. Setting a global property can be used by plugins to save their internal parameters. Plugins are only allowed to set properties whose index are above or equal to 1024 (properties below 1024 are read-only and reserved by Orthanc).

    Args:
      property (int): The global property of interest.
      value (str): The value to be set in the global property.
    """
    ...

# This function sets the value of an integer metrics to monitor the behavior of the plugin through tools such as Prometheus
def SetMetricsIntegerValue(name: str, value: int, type: MetricsType) -> None:
    """
    This function sets the value of an integer metrics to monitor the behavior of the plugin through tools such as Prometheus. The values of all the metrics are stored within the Orthanc context.

    Args:
      name (str): The name of the metrics to be set.
      value (int): The value of the metrics.
      type (MetricsType): The type of the metrics. This parameter is only taken into consideration the first time this metrics is set.
    """
    ...

# This function sets the value of a floating-point metrics to monitor the behavior of the plugin through tools such as Prometheus
def SetMetricsValue(name: str, value: float, type: MetricsType) -> None:
    """
    This function sets the value of a floating-point metrics to monitor the behavior of the plugin through tools such as Prometheus. The values of all the metrics are stored within the Orthanc context.

    Args:
      name (str): The name of the metrics to be set.
      value (float): The value of the metrics.
      type (MetricsType): The type of the metrics. This parameter is only taken into consideration the first time this metrics is set.
    """
    ...

# For plugins that come with a Web interface, this function declares the entry path where to find this interface
def SetRootUri(uri: str) -> None:
    """
    For plugins that come with a Web interface, this function declares the entry path where to find this interface. This information is notably used in the "Plugins" page of Orthanc Explorer.

    Args:
      uri (str): The root URI for this plugin.
    """
    ...

# For plugins that come with a Web interface, this function declares the entry path where to find this interface
def SetRootUri2(plugin: str, uri: str) -> None:
    """
    For plugins that come with a Web interface, this function declares the entry path where to find this interface. This information is notably used in the "Plugins" page of Orthanc Explorer.

    Args:
      plugin (str): Identifier of your plugin (it must match "OrthancPluginGetName()").
      uri (str): The root URI for this plugin.
    """
    ...

def StoreKeyValue(store_id: str, key: str, value: bytes) -> None:
    """

    Args:
      store_id (str): A unique identifier identifying both the plugin and the key-value store.
      key (str): The key of the value to store (note: storeId + key must be unique).
      value (bytes): The value to store.
    """
    ...

# This function parses a memory buffer that contains a DICOM file, then transcodes it to the given transfer syntax
def TranscodeDicomInstance(buffer: bytes, transfer_syntax: str) -> DicomInstance:
    """
    This function parses a memory buffer that contains a DICOM file, then transcodes it to the given transfer syntax. The function returns a new pointer to a data structure that is managed by the Orthanc core.

    Args:
      buffer (bytes): The memory buffer containing the DICOM instance.
      transfer_syntax (str): The transfer syntax UID for the transcoding.

    Returns:
      DicomInstance: The newly allocated DICOM instance. It must be freed with OrthancPluginFreeDicomInstance().
    """
    ...

# This function decodes a compressed image from a memory buffer
def UncompressImage(data: bytes, format: ImageFormat) -> Image:
    """
    This function decodes a compressed image from a memory buffer.

    Args:
      data (bytes): Pointer to a memory buffer containing the compressed image.
      format (ImageFormat): The file format of the compressed image.

    Returns:
      Image: The uncompressed image. It must be freed with OrthancPluginFreeImage().
    """
    ...

# Write the content of a memory buffer to the filesystem
def WriteFile(path: str, data: bytes) -> None:
    """
    Write the content of a memory buffer to the filesystem.

    Args:
      path (str): The path of the file to be written.
      data (bytes): The content of the memory buffer.
    """
    ...

# This function creates an image of given size and format, and initializes its pixel data from a memory buffer
def CreateImageFromBuffer(format: PixelFormat, width: int, height: int, pitch: int, buffer: bytes) -> Image:
    """
    This function creates an image of given size and format, and initializes its pixel data from a memory buffer.

    Args:
      format (PixelFormat): The format of the pixels.
      width (int): The width of the image.
      height (int): The height of the image.
      pitch (int): The pitch of the image (i.e. the number of bytes between 2 successive lines of the image in the memory buffer).
      buffer (bytes): The memory buffer.

    Returns:
      Image: The newly allocated image.
    """
    ...

# Dequeue a value from a queue
def DequeueValue(queue_id: str, origin: QueueOrigin) -> bytes:
    """
    Dequeue a value from a queue.

    Args:
      queue_id (str): The identifier of the queue.
      origin (QueueOrigin): The position from where the value is dequeued (back for LIFO, front for FIFO).

    Returns:
      bytes: The value, or None if no more value is available.
    """
    ...

# Get the value associated with a key in the Orthanc key-value store
def GetKeyValue(store_id: str, key: str) -> bytes:
    """
    Get the value associated with a key in the Orthanc key-value store.

    Args:
      store_id (str): The identifier of the key-value store.
      key (str): The key.

    Returns:
      bytes: The value, or None.
    """
    ...

# Get the number of elements in a queue
def GetQueueSize(queue_id: str) -> int:
    """
    Get the number of elements in a queue.

    Args:
      queue_id (str): The identifier of the queue.

    Returns:
      int: The value, or None.
    """
    ...

# Get information about the given DICOM tag
def LookupDictionary(name: str) -> dict:
    """
    Get information about the given DICOM tag.

    Args:
      name (str): The name of the DICOM tag.

    Returns:
      dict: Dictionary containing the requested information.
    """
    ...

class FindCallback(typing.Protocol):
    def __call__(self, answers: FindAnswers, query: FindQuery, issuer_aet: str, called_aet: str) -> None:
        ...

# Register a callback to handle C-Find requests
def RegisterFindCallback(callback: FindCallback) -> None:
    """
    Register a callback to handle C-Find requests.

    Args:
      callback (FindCallback): The callback function.
    """
    ...

class FindCallback2(typing.Protocol):
    def __call__(self, answers: FindAnswers, query: FindQuery, connection: DicomConnection) -> None:
        ...

# Register a callback to handle C-Find requests (v2)
def RegisterFindCallback2(callback: FindCallback2) -> None:
    """
    Register a callback to handle C-Find requests (v2).

    Args:
      callback (FindCallback2): The callback function.
    """
    ...

class IncomingCStoreInstanceFilter(typing.Protocol):
    def __call__(self, received_dicom: DicomInstance) -> int:
        ...

# Register a callback to filter incoming DICOM instances received by Orthanc through C-STORE
def RegisterIncomingCStoreInstanceFilter(callback: IncomingCStoreInstanceFilter) -> None:
    """
    Register a callback to filter incoming DICOM instances received by Orthanc through C-STORE.

    Args:
      callback (IncomingCStoreInstanceFilter): The callback function.
    """
    ...

class IncomingHttpRequestFilter(typing.Protocol):
    def __call__(self, uri: str, method: HttpMethod, ip: str, headers: dict, get: dict) -> bool:
        ...

# Callback to filter incoming HTTP requests received by Orthanc
def RegisterIncomingHttpRequestFilter(callback: IncomingHttpRequestFilter) -> None:
    """
    Callback to filter incoming HTTP requests received by Orthanc.

    Args:
      callback (IncomingHttpRequestFilter): The callback function.
    """
    ...

class MoveCallback(typing.Protocol):
    def __call__(self, Level: str, PatientID: str, AccessionNumber: str, StudyInstanceUID: str, SeriesInstanceUID: str, SOPInstanceUID: str, OriginatorAET: str, SourceAET: str, TargetAET: str, OriginatorID: int) -> None:
        ...

# Register a callback to handle C-Move requests (simple version, with 1 suboperation)
def RegisterMoveCallback(callback: MoveCallback) -> None:
    """
    Register a callback to handle C-Move requests (simple version, with 1 suboperation).

    Args:
      callback (MoveCallback): The callback function.
    """
    ...

class MoveCallback2(typing.Protocol):
    def __call__(self, Level: str, PatientID: str, AccessionNumber: str, StudyInstanceUID: str, SeriesInstanceUID: str, SOPInstanceUID: str, OriginatorAET: str, SourceAET: str, TargetAET: str, OriginatorID: int) -> object:
        ...

class GetMoveSizeCallback(typing.Protocol):
    def __call__(self, driver: object) -> int:
        ...

class ApplyMoveCallback(typing.Protocol):
    def __call__(self, driver: object) -> None:
        ...

class FreeMoveCallback(typing.Protocol):
    def __call__(self, driver: object) -> None:
        ...

# Register a callback to handle C-Move requests (full version, with multiple suboperations
def RegisterMoveCallback2(callback: MoveCallback2, get_move_size: GetMoveSizeCallback, apply_move: ApplyMoveCallback, free_move: FreeMoveCallback) -> None:
    """
    Register a callback to handle C-Move requests (full version, with multiple suboperations.  Equivalent to the OrthancPluginRegisterMoveCallback from the C SDK).

    Args:
      callback (MoveCallback2): Main callback that creates the C-Move driver.
      get_move_size (GetMoveSizeCallback): Callback to read the number of C-Move suboperations.
      apply_move (ApplyMoveCallback): Callback to apply one C-Move suboperation.
      free_move (FreeMoveCallback): Callback to free the C-Move driver.
    """
    ...

class MoveCallback3(typing.Protocol):
    def __call__(self, Connection: DicomConnection, Level: str, PatientID: str, AccessionNumber: str, StudyInstanceUID: str, SeriesInstanceUID: str, SOPInstanceUID: str, TargetAET: str, OriginatorID: int) -> object:
        ...

class GetMoveSizeCallback(typing.Protocol):
    def __call__(self, driver: object) -> int:
        ...

class ApplyMoveCallback(typing.Protocol):
    def __call__(self, driver: object) -> None:
        ...

class FreeMoveCallback(typing.Protocol):
    def __call__(self, driver: object) -> None:
        ...

# Register a callback to handle C-Move requests (full version, with multiple suboperations
def RegisterMoveCallback3(callback: MoveCallback3, get_move_size: GetMoveSizeCallback, apply_move: ApplyMoveCallback, free_move: FreeMoveCallback) -> None:
    """
    Register a callback to handle C-Move requests (full version, with multiple suboperations.  Equivalent to the OrthancPluginRegisterMoveCallbeck2 from the C SDK).

    Args:
      callback (MoveCallback3): Main callback that creates the C-Move driver.
      get_move_size (GetMoveSizeCallback): Callback to read the number of C-Move suboperations.
      apply_move (ApplyMoveCallback): Callback to apply one C-Move suboperation.
      free_move (FreeMoveCallback): Callback to free the C-Move driver.
    """
    ...

class OnChangeCallback(typing.Protocol):
    def __call__(self, change_type: ChangeType, resource_type: ResourceType, resource_id: str) -> None:
        ...

# Register a callback to monitor changes
def RegisterOnChangeCallback(callback: OnChangeCallback) -> None:
    """
    Register a callback to monitor changes.

    Args:
      callback (OnChangeCallback): The callback function.
    """
    ...

class OnStoredInstanceCallback(typing.Protocol):
    def __call__(self, instance: DicomInstance, instance_id: str) -> None:
        ...

# Register a callback for received DICOM instances
def RegisterOnStoredInstanceCallback(callback: OnStoredInstanceCallback) -> None:
    """
    Register a callback for received DICOM instances.

    Args:
      callback (OnStoredInstanceCallback): The callback function.
    """
    ...

class ReceivedInstanceCallback(typing.Protocol):
    def __call__(self, received_dicom: bytes, origin: InstanceOrigin) -> tuple[ReceivedInstanceAction, bytes]:
        ...

# Register a callback to keep/discard/modify a DICOM instance received by Orthanc from any source (C-STORE or REST API)
def RegisterReceivedInstanceCallback(callback: ReceivedInstanceCallback) -> None:
    """
    Register a callback to keep/discard/modify a DICOM instance received by Orthanc from any source (C-STORE or REST API).

    Args:
      callback (ReceivedInstanceCallback): The callback function.
    """
    ...

class RestCallback(typing.Protocol):
    def __call__(self, output: RestOutput, url: str, method: HttpMethod, groups: dict, get: dict, headers: dict, body: bytes=None) -> None:
        ...

# Register a REST callback
def RegisterRestCallback(path_regular_expression: str, callback: RestCallback) -> None:
    """
    Register a REST callback.

    Args:
      path_regular_expression (str): Regular expression for the URI. May contain groups.
      callback (RestCallback): The callback function to handle the REST call.
    """
    ...

class StorageCreateCallback(typing.Protocol):
    def __call__(self, uuid: str, content_type: ContentType, data: bytes) -> None:
        ...

class StorageReadCallback(typing.Protocol):
    def __call__(self, uuid: str, content_type: ContentType) -> bytes:
        ...

class StorageRemoveCallback(typing.Protocol):
    def __call__(self, uuid: str, content_type: ContentType) -> None:
        ...

# Register a custom storage area
def RegisterStorageArea(create: StorageCreateCallback, read: StorageReadCallback, remove: StorageRemoveCallback) -> None:
    """
    Register a custom storage area.

    Args:
      create (StorageCreateCallback): The callback function to store a file on the custom storage area.
      read (StorageReadCallback): The callback function to read a file from the custom storage area.
      remove (StorageRemoveCallback): The callback function to remove a file from the custom storage area.
    """
    ...

class StorageCreateCallback2(typing.Protocol):
    def __call__(self, uuid: str, content_type: ContentType, compression_type: CompressionType, content: bytes, dicom_instance: DicomInstance) -> Tuple:
        ...

class StorageReadCallback2(typing.Protocol):
    def __call__(self, uuid: str, content_type: ContentType, range_start: int, size: int, custom_data: bytes) -> Tuple:
        ...

class StorageRemoveCallback2(typing.Protocol):
    def __call__(self, uuid: str, content_type: ContentType, custom_data: bytes) -> ErrorCode:
        ...

# Register a custom storage area (v3)
def RegisterStorageArea3(create: StorageCreateCallback2, read: StorageReadCallback2, remove: StorageRemoveCallback2) -> None:
    """
    Register a custom storage area (v3).

    Args:
      create (StorageCreateCallback2): The callback function to store a file on the custom storage area (v2).
      read (StorageReadCallback2): The callback function to read a file from the custom storage area (v2).
      remove (StorageRemoveCallback2): The callback function to remove a file from the custom storage area (v2).
    """
    ...

class StorageCommitmentScpCallback(typing.Protocol):
    def __call__(self, job_id: str, transaction_uid: str, sop_class_uids: list[str], sop_instance_uids: list[str], remote_aet: str, called_aet: str) -> object:
        ...

class StorageCommitmentLookup(typing.Protocol):
    def __call__(self, sop_class_uid: str, sop_instance_uid: str, driver: object) -> StorageCommitmentFailureReason:
        ...

# Register a callback to handle incoming requests to the storage commitment SCP
def RegisterStorageCommitmentScpCallback(callback: StorageCommitmentScpCallback, lookup: StorageCommitmentLookup) -> None:
    """
    Register a callback to handle incoming requests to the storage commitment SCP.

    Args:
      callback (StorageCommitmentScpCallback): Main callback that creates the a driver to handle an incoming storage commitment request.
      lookup (StorageCommitmentLookup): Callback function to get the status of one DICOM instance.
    """
    ...

class StorageCommitmentScpCallback2(typing.Protocol):
    def __call__(self, job_id: str, transaction_uid: str, sop_class_uids: list[str], sop_instance_uids: list[str], connection: DicomConnection) -> object:
        ...

class StorageCommitmentLookup(typing.Protocol):
    def __call__(self, sop_class_uid: str, sop_instance_uid: str, driver: object) -> StorageCommitmentFailureReason:
        ...

# Register a callback to handle incoming requests to the storage commitment SCP (v2)
def RegisterStorageCommitmentScpCallback2(callback: StorageCommitmentScpCallback2, lookup: StorageCommitmentLookup) -> None:
    """
    Register a callback to handle incoming requests to the storage commitment SCP (v2).

    Args:
      callback (StorageCommitmentScpCallback2): Main callback that creates the a driver to handle an incoming storage commitment request.
      lookup (StorageCommitmentLookup): Callback function to get the status of one DICOM instance.
    """
    ...

class WorklistCallback(typing.Protocol):
    def __call__(self, answers: WorklistAnswers, query: WorklistQuery, issuer_aet: str, called_aet: str) -> None:
        ...

# Register a callback to handle modality worklists requests
def RegisterWorklistCallback(callback: WorklistCallback) -> None:
    """
    Register a callback to handle modality worklists requests.

    Args:
      callback (WorklistCallback): The callback function.
    """
    ...

class WorklistCallback2(typing.Protocol):
    def __call__(self, answers: WorklistAnswers, query: WorklistQuery, connection: DicomConnection) -> None:
        ...

# Register a callback to handle modality worklists requests (v2)
def RegisterWorklistCallback2(callback: WorklistCallback2) -> None:
    """
    Register a callback to handle modality worklists requests (v2).

    Args:
      callback (WorklistCallback2): The callback function.
    """
    ...

# Reserve a value from a queue
def ReserveQueueValue(queue_id: str, origin: QueueOrigin, release_timeout: int) -> tuple:
    """
    Reserve a value from a queue.

    Args:
      queue_id (str): The identifier of the queue.
      origin (QueueOrigin): The position from where the value is reserved (back for LIFO, front for FIFO).
      release_timeout (int): The duration (in seconds) after which the value is released if not acknowledged.

    Returns:
      tuple: A tuple with (The value, or None if no more value is available + a value id that can be used to acknowledge the value).
    """
    ...

# Change the Stable status of a resource
def SetStableStatus(resource_id: str, stable_status: StableStatus) -> tuple:
    """
    Change the Stable status of a resource

    Args:
      resource_id (str): The identifier of the resource.
      stable_status (StableStatus): The new stable status: 0 for Stable, 1 for Unstable.

    Returns:
      tuple: A tuple with (The error code, An integer indicating whether the status has changed (1) or not (0) during the execution of this command).
    """
    ...


class DicomConnection:
    """
    DICOM connection managed by the Orthanc core
    """
    ...

    
    # This function returns the Application Entity Title (AET) of the DICOM modality from which a DICOM connection originates
    def GetConnectionRemoteAet(self) -> str:
        """
        This function returns the Application Entity Title (AET) of the DICOM modality from which a DICOM connection originates.

        Returns:
          str: The pointer to the AET, NULL in case of error.
        """
        ...
    
    # This function returns the IP of the DICOM modality from which a DICOM connection originates
    def GetConnectionRemoteIp(self) -> str:
        """
        This function returns the IP of the DICOM modality from which a DICOM connection originates.

        Returns:
          str: The pointer to the IP, NULL in case of error.
        """
        ...
    
    # This function returns the AET that was called by the remote DICOM modality over a DICOM connection
    def GetConnectionCalledAet(self) -> str:
        """
        This function returns the AET that was called by the remote DICOM modality over a DICOM connection. This corresponds to one of the AETs used by Orthanc.

        Returns:
          str: The pointer to the called AET, NULL in case of error.
        """
        ...

class DicomInstance:
    """
    DICOM instance managed by the Orthanc core
    """
    ...

    
    # This function returns the Application Entity Title (AET) of the DICOM modality from which a DICOM instance originates
    def GetInstanceRemoteAet(self) -> str:
        """
        This function returns the Application Entity Title (AET) of the DICOM modality from which a DICOM instance originates.

        Returns:
          str: The AET if success, NULL if error.
        """
        ...
    
    # This function returns the number of bytes of the given DICOM instance
    def GetInstanceSize(self) -> int:
        """
        This function returns the number of bytes of the given DICOM instance.

        Returns:
          int: The size of the file, -1 in case of error.
        """
        ...
    
    # This function returns a pointer to a newly created string containing a JSON file
    def GetInstanceJson(self) -> str:
        """
        This function returns a pointer to a newly created string containing a JSON file. This JSON file encodes the tag hierarchy of the given DICOM instance.

        Returns:
          str: The NULL value in case of error, or a string containing the JSON file. This string must be freed by OrthancPluginFreeString().
        """
        ...
    
    # This function returns a pointer to a newly created string containing a JSON file
    def GetInstanceSimplifiedJson(self) -> str:
        """
        This function returns a pointer to a newly created string containing a JSON file. This JSON file encodes the tag hierarchy of the given DICOM instance. In contrast with ::OrthancPluginGetInstanceJson(), the returned JSON file is in its simplified version.

        Returns:
          str: The NULL value in case of error, or a string containing the JSON file. This string must be freed by OrthancPluginFreeString().
        """
        ...
    
    # This function checks whether the DICOM instance of interest is associated with some metadata
    def HasInstanceMetadata(self, metadata: str) -> int:
        """
        This function checks whether the DICOM instance of interest is associated with some metadata. As of Orthanc 0.8.1, in the callbacks registered by ::OrthancPluginRegisterOnStoredInstanceCallback(), the only possibly available metadata are "ReceptionDate", "RemoteAET" and "IndexInSeries".

        Args:
          metadata (str): The metadata of interest.

        Returns:
          int: 1 if the metadata is present, 0 if it is absent, -1 in case of error.
        """
        ...
    
    # This functions returns the value of some metadata that is associated with the DICOM instance of interest
    def GetInstanceMetadata(self, metadata: str) -> str:
        """
        This functions returns the value of some metadata that is associated with the DICOM instance of interest. Before calling this function, the existence of the metadata must have been checked with ::OrthancPluginHasInstanceMetadata().

        Args:
          metadata (str): The metadata of interest.

        Returns:
          str: The metadata value if success, NULL if error. Please note that the returned string belongs to the instance object and must NOT be deallocated. Please make a copy of the string if you wish to access it later.
        """
        ...
    
    # This function returns the origin of a DICOM instance that has been received by Orthanc
    def GetInstanceOrigin(self) -> InstanceOrigin:
        """
        This function returns the origin of a DICOM instance that has been received by Orthanc.

        Returns:
          InstanceOrigin: The origin of the instance.
        """
        ...
    
    # This function returns a pointer to a newly created string that contains the transfer syntax UID of the DICOM instance
    def GetInstanceTransferSyntaxUid(self) -> str:
        """
        This function returns a pointer to a newly created string that contains the transfer syntax UID of the DICOM instance. The empty string might be returned if this information is unknown.

        Returns:
          str: The NULL value in case of error, or a string containing the transfer syntax UID. This string must be freed by OrthancPluginFreeString().
        """
        ...
    
    # This function returns a Boolean value indicating whether the DICOM instance contains the pixel data (7FE0,0010) tag
    def HasInstancePixelData(self) -> int:
        """
        This function returns a Boolean value indicating whether the DICOM instance contains the pixel data (7FE0,0010) tag.

        Returns:
          int: "1" if the DICOM instance contains pixel data, or "0" if the tag is missing, or "-1" in the case of an error.
        """
        ...
    
    # This function returns the number of frames that are part of a DICOM image managed by the Orthanc core
    def GetInstanceFramesCount(self) -> int:
        """
        This function returns the number of frames that are part of a DICOM image managed by the Orthanc core.

        Returns:
          int: The number of frames (will be zero in the case of an error).
        """
        ...
    
    # This function returns a memory buffer containing the raw content of a frame in a DICOM instance that is managed by the Orthanc core
    def GetInstanceRawFrame(self, frame_index: int) -> bytes:
        """
        This function returns a memory buffer containing the raw content of a frame in a DICOM instance that is managed by the Orthanc core. This is notably useful for compressed transfer syntaxes, as it gives access to the embedded files (such as JPEG, JPEG-LS or JPEG2k). The Orthanc core transparently reassembles the fragments to extract the raw frame.

        Args:
          frame_index (int): The index of the frame of interest.

        Returns:
          bytes: 0 if success, or the error code if failure.
        """
        ...
    
    # This function decodes one frame of a DICOM image that is managed by the Orthanc core
    def GetInstanceDecodedFrame(self, frame_index: int) -> Image:
        """
        This function decodes one frame of a DICOM image that is managed by the Orthanc core.

        Args:
          frame_index (int): The index of the frame of interest.

        Returns:
          Image: The uncompressed image. It must be freed with OrthancPluginFreeImage().
        """
        ...
    
    # This function returns a memory buffer containing the serialization of a DICOM instance that is managed by the Orthanc core
    def SerializeDicomInstance(self) -> bytes:
        """
        This function returns a memory buffer containing the serialization of a DICOM instance that is managed by the Orthanc core.

        Returns:
          bytes: 0 if success, or the error code if failure.
        """
        ...
    
    # This function takes as DICOM instance managed by the Orthanc core, and outputs a JSON string representing the tags of this DICOM file
    def GetInstanceAdvancedJson(self, format: DicomToJsonFormat, flags: DicomToJsonFlags, max_string_length: int) -> str:
        """
        This function takes as DICOM instance managed by the Orthanc core, and outputs a JSON string representing the tags of this DICOM file.

        Args:
          format (DicomToJsonFormat): The output format.
          flags (DicomToJsonFlags): Flags governing the output.
          max_string_length (int): The maximum length of a field. Too long fields will be output as "null". The 0 value means no maximum length.

        Returns:
          str: The NULL value if the case of an error, or the JSON string. This string must be freed by OrthancPluginFreeString().
        """
        ...

    
    # Get the content of the DICOM instance
    def GetInstanceData(self) -> bytes:
        """
        Get the content of the DICOM instance.

        Returns:
          bytes: The DICOM data.
        """
        ...
class DicomWebNode:
    """
    Node visited by DICOMweb conversion
    """
    ...


class FindAnswers:
    """
    Answers to a DICOM C-FIND query
    """
    ...

    
    # This function adds one answer (encoded as a DICOM file) to the set of answers corresponding to some C-Find SCP request that is not related to modality worklists
    def FindAddAnswer(self, dicom: bytes) -> None:
        """
        This function adds one answer (encoded as a DICOM file) to the set of answers corresponding to some C-Find SCP request that is not related to modality worklists.

        Args:
          dicom (bytes): The answer to be added, encoded as a DICOM file.
        """
        ...
    
    # This function marks as incomplete the set of answers corresponding to some C-Find SCP request that is not related to modality worklists
    def FindMarkIncomplete(self) -> None:
        """
        This function marks as incomplete the set of answers corresponding to some C-Find SCP request that is not related to modality worklists. This must be used if canceling the handling of a request when too many answers are to be returned.
        """
        ...

class FindMatcher:
    """
    Matcher for DICOM C-FIND query
    """
    ...

    
    # This function checks whether one DICOM instance matches C-Find matcher that was previously allocated using OrthancPluginCreateFindMatcher()
    def IsMatch(self, dicom: bytes) -> int:
        """
        This function checks whether one DICOM instance matches C-Find matcher that was previously allocated using OrthancPluginCreateFindMatcher().

        Args:
          dicom (bytes): The DICOM instance to be matched.

        Returns:
          int: 1 if the DICOM instance matches the query, 0 otherwise.
        """
        ...

class FindQuery:
    """
    DICOM C-FIND query
    """
    ...

    
    # This function returns the number of tags that are contained in the given C-Find query
    def GetFindQuerySize(self) -> int:
        """
        This function returns the number of tags that are contained in the given C-Find query.

        Returns:
          int: The number of tags.
        """
        ...
    
    # This function returns the symbolic name of one DICOM tag in the given C-Find query
    def GetFindQueryTagName(self, index: int) -> str:
        """
        This function returns the symbolic name of one DICOM tag in the given C-Find query.

        Args:
          index (int): The index of the tag of interest.

        Returns:
          str: 0 if success, other value if error.
        """
        ...
    
    # This function returns the value associated with one tag in the given C-Find query
    def GetFindQueryValue(self, index: int) -> str:
        """
        This function returns the value associated with one tag in the given C-Find query.

        Args:
          index (int): The index of the tag of interest.

        Returns:
          str: 0 if success, other value if error.
        """
        ...

    
    # This function returns the element of one DICOM tag in the given C-Find query
    def GetFindQueryTagElement(self, index: int) -> int:
        """
        This function returns the element of one DICOM tag in the given C-Find query.

        Args:
          index (int): The index of the tag of interest.

        Returns:
          int: The value of the element.
        """
        ...
    
    # This function returns the group of one DICOM tag in the given C-Find query
    def GetFindQueryTagGroup(self, index: int) -> int:
        """
        This function returns the group of one DICOM tag in the given C-Find query.

        Args:
          index (int): The index of the tag of interest.

        Returns:
          int: The value of the group.
        """
        ...
class Image:
    """
    2D image managed by the Orthanc core
    """
    ...

    
    # This function returns the type of memory layout for the pixels of the given image
    def GetImagePixelFormat(self) -> PixelFormat:
        """
        This function returns the type of memory layout for the pixels of the given image.

        Returns:
          PixelFormat: The pixel format.
        """
        ...
    
    # This function returns the width of the given image
    def GetImageWidth(self) -> int:
        """
        This function returns the width of the given image.

        Returns:
          int: The width.
        """
        ...
    
    # This function returns the height of the given image
    def GetImageHeight(self) -> int:
        """
        This function returns the height of the given image.

        Returns:
          int: The height.
        """
        ...
    
    # This function returns the pitch of the given image
    def GetImagePitch(self) -> int:
        """
        This function returns the pitch of the given image. The pitch is defined as the number of bytes between 2 successive lines of the image in the memory buffer.

        Returns:
          int: The pitch.
        """
        ...
    
    # This function creates a new image, changing the memory layout of the pixels
    def ConvertPixelFormat(self, target_format: PixelFormat) -> Image:
        """
        This function creates a new image, changing the memory layout of the pixels.

        Args:
          target_format (PixelFormat): The target pixel format.

        Returns:
          Image: The resulting image. It must be freed with OrthancPluginFreeImage().
        """
        ...
    
    # This function draws some text on some image
    def DrawText(self, font_index: int, utf8_text: str, x: int, y: int, r: int, g: int, b: int) -> None:
        """
        This function draws some text on some image.

        Args:
          font_index (int): The index of the font. This value must be less than OrthancPluginGetFontsCount().
          utf8_text (str): The text to be drawn, encoded as an UTF-8 zero-terminated string.
          x (int): The X position of the text over the image.
          y (int): The Y position of the text over the image.
          r (int): The value of the red color channel of the text.
          g (int): The value of the green color channel of the text.
          b (int): The value of the blue color channel of the text.
        """
        ...

    
    # This function returns a pointer to the memory buffer that contains the pixels of the image
    def GetImageBuffer(self) -> bytes:
        """
        This function returns a pointer to the memory buffer that contains the pixels of the image.

        Returns:
          bytes: The pixel data.
        """
        ...
class Job:
    """
    Orthanc job
    """
    ...

    
    # This function adds the given job to the pending jobs of Orthanc
    def SubmitJob(self, priority: int) -> str:
        """
        This function adds the given job to the pending jobs of Orthanc. Orthanc will take take of freeing it by invoking the finalization callback provided to OrthancPluginCreateJob().

        Args:
          priority (int): The priority of the job.

        Returns:
          str: ID of the newly-submitted job. This string must be freed by OrthancPluginFreeString().
        """
        ...

class KeysValuesIterator:
    """
    Iterator over the keys and values of a key-value store
    """
    ...

    
    # Before using this function, the function OrthancPluginKeysValuesIteratorNext() must have been called at least once
    def GetKey(self) -> str:
        """
        Before using this function, the function OrthancPluginKeysValuesIteratorNext() must have been called at least once.

        Returns:
          str: The current key, or NULL in the case of an error.
        """
        ...
    
    # Before using this function, the function OrthancPluginKeysValuesIteratorNext() must have been called at least once
    def GetValue(self) -> bytes:
        """
        Before using this function, the function OrthancPluginKeysValuesIteratorNext() must have been called at least once.

        Returns:
          bytes: The current value, or NULL in the case of an error.
        """
        ...

    
    # Advance to the next element in the iterator
    def Next(self) -> bool:
        """
        Advance to the next element in the iterator.

        Returns:
          bool: Whether the iterator is done.
        """
        ...
class Peers:
    """
    Orthanc peer
    """
    ...

    
    # This function returns the number of Orthanc peers
    def GetPeersCount(self) -> int:
        """
        This function returns the number of Orthanc peers.
        This function is thread-safe: Several threads sharing the same OrthancPluginPeers object can simultaneously call this function.

        Returns:
          int: The number of peers.
        """
        ...
    
    # This function returns the symbolic name of the Orthanc peer, which corresponds to the key of the "OrthancPeers" configuration option of Orthanc
    def GetPeerName(self, peer_index: int) -> str:
        """
        This function returns the symbolic name of the Orthanc peer, which corresponds to the key of the "OrthancPeers" configuration option of Orthanc.
        This function is thread-safe: Several threads sharing the same OrthancPluginPeers object can simultaneously call this function.

        Args:
          peer_index (int): The index of the peer of interest. This value must be lower than OrthancPluginGetPeersCount().

        Returns:
          str: The symbolic name, or NULL in the case of an error.
        """
        ...
    
    # This function returns the base URL to the REST API of some Orthanc peer
    def GetPeerUrl(self, peer_index: int) -> str:
        """
        This function returns the base URL to the REST API of some Orthanc peer.
        This function is thread-safe: Several threads sharing the same OrthancPluginPeers object can simultaneously call this function.

        Args:
          peer_index (int): The index of the peer of interest. This value must be lower than OrthancPluginGetPeersCount().

        Returns:
          str: The URL, or NULL in the case of an error.
        """
        ...
    
    # This function returns some user-defined property of some Orthanc peer
    def GetPeerUserProperty(self, peer_index: int, user_property: str) -> str:
        """
        This function returns some user-defined property of some Orthanc peer. An user-defined property is a property that is associated with the peer in the Orthanc configuration file, but that is not recognized by the Orthanc core.
        This function is thread-safe: Several threads sharing the same OrthancPluginPeers object can simultaneously call this function.

        Args:
          peer_index (int): The index of the peer of interest. This value must be lower than OrthancPluginGetPeersCount().
          user_property (str): The user property of interest.

        Returns:
          str: The value of the user property, or NULL if it is not defined.
        """
        ...

class RestOutput:
    """
    Output for a call to the REST API of Orthanc
    """
    ...

    
    # This function answers to a REST request with the content of a memory buffer
    def AnswerBuffer(self, answer: bytes, mime_type: str) -> None:
        """
        This function answers to a REST request with the content of a memory buffer.

        Args:
          answer (bytes): Pointer to the memory buffer containing the answer.
          mime_type (str): The MIME type of the answer.
        """
        ...
    
    # This function answers to a REST request with a PNG image
    def CompressAndAnswerPngImage(self, format: PixelFormat, width: int, height: int, pitch: int, buffer: bytes) -> None:
        """
        This function answers to a REST request with a PNG image. The parameters of this function describe a memory buffer that contains an uncompressed image. The image will be automatically compressed as a PNG image by the core system of Orthanc.

        Args:
          format (PixelFormat): The memory layout of the uncompressed image.
          width (int): The width of the image.
          height (int): The height of the image.
          pitch (int): The pitch of the image (i.e. the number of bytes between 2 successive lines of the image in the memory buffer).
          buffer (bytes): The memory buffer containing the uncompressed image.
        """
        ...
    
    # This function answers to a REST request by redirecting the user to another URI using HTTP status 301
    def Redirect(self, redirection: str) -> None:
        """
        This function answers to a REST request by redirecting the user to another URI using HTTP status 301.

        Args:
          redirection (str): Where to redirect.
        """
        ...
    
    # This function answers to a REST request by sending a HTTP status code (such as "400 - Bad Request")
    def SendHttpStatusCode(self, status: int) -> None:
        """
        This function answers to a REST request by sending a HTTP status code (such as "400 - Bad Request"). Note that: - Successful requests (status 200) must use ::OrthancPluginAnswerBuffer(). - Redirections (status 301) must use ::OrthancPluginRedirect(). - Unauthorized access (status 401) must use ::OrthancPluginSendUnauthorized(). - Methods not allowed (status 405) must use ::OrthancPluginSendMethodNotAllowed().

        Args:
          status (int): The HTTP status code to be sent.
        """
        ...
    
    # This function answers to a REST request by signaling that it is not authorized
    def SendUnauthorized(self, realm: str) -> None:
        """
        This function answers to a REST request by signaling that it is not authorized.

        Args:
          realm (str): The realm for the authorization process.
        """
        ...
    
    # This function answers to a REST request by signaling that the queried URI does not support this method
    def SendMethodNotAllowed(self, allowed_methods: str) -> None:
        """
        This function answers to a REST request by signaling that the queried URI does not support this method.

        Args:
          allowed_methods (str): The allowed methods for this URI (e.g. "GET,POST" after a PUT or a POST request).
        """
        ...
    
    # This function sets a cookie in the HTTP client
    def SetCookie(self, cookie: str, value: str) -> None:
        """
        This function sets a cookie in the HTTP client.

        Args:
          cookie (str): The cookie to be set.
          value (str): The value of the cookie.
        """
        ...
    
    # This function sets a HTTP header in the HTTP answer
    def SetHttpHeader(self, key: str, value: str) -> None:
        """
        This function sets a HTTP header in the HTTP answer.

        Args:
          key (str): The HTTP header to be set.
          value (str): The value of the HTTP header.
        """
        ...
    
    # Initiates a HTTP multipart answer, as the result of a REST request
    def StartMultipartAnswer(self, sub_type: str, content_type: str) -> None:
        """
        Initiates a HTTP multipart answer, as the result of a REST request.

        Args:
          sub_type (str): The sub-type of the multipart answer ("mixed" or "related").
          content_type (str): The MIME type of the items in the multipart answer.
        """
        ...
    
    # This function sends an item as a part of some HTTP multipart answer that was initiated by OrthancPluginStartMultipartAnswer()
    def SendMultipartItem(self, answer: bytes) -> None:
        """
        This function sends an item as a part of some HTTP multipart answer that was initiated by OrthancPluginStartMultipartAnswer().

        Args:
          answer (bytes): Pointer to the memory buffer containing the item.
        """
        ...
    
    # This function answers to a HTTP request by sending a HTTP status code (such as "400 - Bad Request"), together with a body describing the error
    def SendHttpStatus(self, status: int, body: bytes) -> None:
        """
        This function answers to a HTTP request by sending a HTTP status code (such as "400 - Bad Request"), together with a body describing the error. The body will only be returned if the configuration option "HttpDescribeErrors" of Orthanc is set to "true".
        Note that: - Successful requests (status 200) must use ::OrthancPluginAnswerBuffer(). - Redirections (status 301) must use ::OrthancPluginRedirect(). - Unauthorized access (status 401) must use ::OrthancPluginSendUnauthorized(). - Methods not allowed (status 405) must use ::OrthancPluginSendMethodNotAllowed().

        Args:
          status (int): The HTTP status code to be sent.
          body (bytes): The body of the answer.
        """
        ...
    
    # This function answers to a REST request with a JPEG image
    def CompressAndAnswerJpegImage(self, format: PixelFormat, width: int, height: int, pitch: int, buffer: bytes, quality: int) -> None:
        """
        This function answers to a REST request with a JPEG image. The parameters of this function describe a memory buffer that contains an uncompressed image. The image will be automatically compressed as a JPEG image by the core system of Orthanc.

        Args:
          format (PixelFormat): The memory layout of the uncompressed image.
          width (int): The width of the image.
          height (int): The height of the image.
          pitch (int): The pitch of the image (i.e. the number of bytes between 2 successive lines of the image in the memory buffer).
          buffer (bytes): The memory buffer containing the uncompressed image.
          quality (int): The quality of the JPEG encoding, between 1 (worst quality, best compression) and 100 (best quality, worst compression).
        """
        ...
    
    # This function sets the detailed description associated with an HTTP error
    def SetHttpErrorDetails(self, details: str, log: int) -> None:
        """
        This function sets the detailed description associated with an HTTP error. This description will be displayed in the "Details" field of the JSON body of the HTTP answer. It is only taken into consideration if the REST callback returns an error code that is different from "OrthancPluginErrorCode_Success", and if the "HttpDescribeErrors" configuration option of Orthanc is set to "true".

        Args:
          details (str): The details of the error message.
          log (int): Whether to also write the detailed error to the Orthanc logs.
        """
        ...
    
    # Initiates an HTTP stream answer, as the result of a REST request
    def StartStreamAnswer(self, content_type: str) -> None:
        """
        Initiates an HTTP stream answer, as the result of a REST request.

        Args:
          content_type (str): The MIME type of the items in the stream answer.
        """
        ...
    
    # This function sends a chunk as part of an HTTP stream answer that was initiated by OrthancPluginStartStreamAnswer()
    def SendStreamChunk(self, answer: bytes) -> None:
        """
        This function sends a chunk as part of an HTTP stream answer that was initiated by OrthancPluginStartStreamAnswer().

        Args:
          answer (bytes): Pointer to the memory buffer containing the item.
        """
        ...

class ServerChunkedRequestReader:
    """
    Read for a chunked HTTP request
    """
    ...


class StorageArea:
    """
    Storage area plugin
    """
    ...

    
    # This function creates a new file inside the storage area that is currently used by Orthanc
    def Create(self, uuid: str, content: bytes, size: int, type: ContentType) -> None:
        """
        This function creates a new file inside the storage area that is currently used by Orthanc.
        Warning: This function will result in a "not implemented" error on versions of the Orthanc core above 1.12.6.

        Args:
          uuid (str): The identifier of the file to be created.
          content (bytes): The content to store in the newly created file.
          size (int): The size of the content.
          type (ContentType): The type of the file content.
        """
        ...
    
    # This function reads the content of a given file from the storage area that is currently used by Orthanc
    def Read(self, uuid: str, type: ContentType) -> bytes:
        """
        This function reads the content of a given file from the storage area that is currently used by Orthanc.
        Warning: This function will result in a "not implemented" error on versions of the Orthanc core above 1.12.6.

        Args:
          uuid (str): The identifier of the file to be read.
          type (ContentType): The type of the file content.

        Returns:
          bytes: 0 if success, other value if error.
        """
        ...
    
    # This function removes a given file from the storage area that is currently used by Orthanc
    def Remove(self, uuid: str, type: ContentType) -> None:
        """
        This function removes a given file from the storage area that is currently used by Orthanc.
        Warning: This function will result in a "not implemented" error on versions of the Orthanc core above 1.12.6.

        Args:
          uuid (str): The identifier of the file to be removed.
          type (ContentType): The type of the file content.
        """
        ...
    
    # This function requests the Orthanc core to reconstruct the main DICOM tags of all the resources of the given type
    def ReconstructMainDicomTags(self, level: ResourceType) -> None:
        """
        This function requests the Orthanc core to reconstruct the main DICOM tags of all the resources of the given type. This function can only be used as a part of the upgrade of a custom database back-end. A database transaction will be automatically setup.

        Args:
          level (ResourceType): The type of the resources of interest.
        """
        ...

class WebDavCollection:
    """
    WebDAV collection
    """
    ...


class WorklistAnswers:
    """
    Answers to a DICOM C-FIND worklist query
    """
    ...

    
    # This function adds one worklist (encoded as a DICOM file) to the set of answers corresponding to some C-Find SCP request against modality worklists
    def WorklistAddAnswer(self, query: WorklistQuery, dicom: bytes) -> None:
        """
        This function adds one worklist (encoded as a DICOM file) to the set of answers corresponding to some C-Find SCP request against modality worklists.

        Args:
          query (WorklistQuery): The worklist query, as received by the callback.
          dicom (bytes): The worklist to answer, encoded as a DICOM file.
        """
        ...
    
    # This function marks as incomplete the set of answers corresponding to some C-Find SCP request against modality worklists
    def WorklistMarkIncomplete(self) -> None:
        """
        This function marks as incomplete the set of answers corresponding to some C-Find SCP request against modality worklists. This must be used if canceling the handling of a request when too many answers are to be returned.
        """
        ...

class WorklistQuery:
    """
    DICOM C-FIND worklist query
    """
    ...

    
    # This function checks whether one worklist (encoded as a DICOM file) matches the C-Find SCP query against modality worklists
    def WorklistIsMatch(self, dicom: bytes) -> int:
        """
        This function checks whether one worklist (encoded as a DICOM file) matches the C-Find SCP query against modality worklists. This function must be called before adding the worklist as an answer through OrthancPluginWorklistAddAnswer().

        Args:
          dicom (bytes): The worklist to answer, encoded as a DICOM file.

        Returns:
          int: 1 if the worklist matches the query, 0 otherwise.
        """
        ...
    
    # This function retrieves the DICOM file that underlies a C-Find SCP query against modality worklists
    def WorklistGetDicomQuery(self) -> bytes:
        """
        This function retrieves the DICOM file that underlies a C-Find SCP query against modality worklists.

        Returns:
          bytes: 0 if success, other value if error.
        """
        ...

