import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
from io import BytesIO
import json
import os
import uuid

import orthanc

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    from pydicom import dcmread, dcmwrite
    from pydicom.dataset import Dataset
except ImportError:
    boto3 = None
    Config = None
    ClientError = None
    dcmread = None
    dcmwrite = None
    Dataset = None


TARGET_TRANSFER_SYNTAX = '1.2.840.10008.1.2.4.50'
LOSSY_QUALITY = 70
COMPRESSION_PROFILE_VERSION = 1
ARCHIVE_BUCKET = os.getenv('LOSSLESS_ARCHIVE_BUCKET')
ARCHIVE_PREFIX = os.getenv('LOSSLESS_ARCHIVE_PREFIX', 'dicom/v1').strip('/')
ARCHIVE_TIMEOUT_SECONDS = os.getenv('LOSSLESS_ARCHIVE_TIMEOUT_SECONDS', '300')
ARCHIVE_WORKERS = os.getenv('LOSSLESS_ARCHIVE_WORKERS', '8')
ARCHIVE_CLIENT = None
ARCHIVE_EXECUTOR = None
LOSSY_TRANSFER_SYNTAXES = {
    '1.2.840.10008.1.2.4.50',
    '1.2.840.10008.1.2.4.51',
    '1.2.840.10008.1.2.4.81',
    '1.2.840.10008.1.2.4.91',
    '1.2.840.10008.1.2.4.203',
}
IDENTITY_TAGS = (
    'PatientID',
    'StudyInstanceUID',
    'SeriesInstanceUID',
    'SOPClassUID',
)


def GetTags(dicom):
    return json.loads(dicom.GetInstanceSimplifiedJson())


def ValidateConfiguration():
    global ARCHIVE_TIMEOUT_SECONDS
    global ARCHIVE_WORKERS

    if dcmread is None or dcmwrite is None or boto3 is None:
        raise RuntimeError('pydicom and boto3 are required for US compression')

    if not ARCHIVE_BUCKET:
        raise RuntimeError('LOSSLESS_ARCHIVE_BUCKET must be configured')
    if not ARCHIVE_PREFIX:
        raise RuntimeError('LOSSLESS_ARCHIVE_PREFIX must not be empty')

    try:
        ARCHIVE_TIMEOUT_SECONDS = int(ARCHIVE_TIMEOUT_SECONDS)
        ARCHIVE_WORKERS = int(ARCHIVE_WORKERS)
    except ValueError as error:
        raise RuntimeError('archive timeout and worker count must be integers') \
            from error

    if ARCHIVE_TIMEOUT_SECONDS <= 0 or ARCHIVE_WORKERS <= 0:
        raise RuntimeError('archive timeout and worker count must be positive')

    configuration = json.loads(orthanc.GetConfiguration())
    quality = configuration.get('DicomLossyTranscodingQuality', 90)
    if quality != LOSSY_QUALITY:
        raise RuntimeError(
            f'DicomLossyTranscodingQuality must be {LOSSY_QUALITY}, got {quality}'
        )

    if (
        configuration.get('IngestTranscoding')
        and configuration.get('IngestTranscodingOfCompressed', True)
    ):
        raise RuntimeError(
            'IngestTranscodingOfCompressed must be false when '
            'IngestTranscoding is configured'
        )


def ConfigureArchiveClient():
    global ARCHIVE_CLIENT
    global ARCHIVE_EXECUTOR

    ARCHIVE_CLIENT = boto3.client(
        's3',
        config=Config(
            connect_timeout=5,
            read_timeout=30,
            retries={'max_attempts': 3, 'mode': 'standard'},
        ),
    )
    ARCHIVE_EXECUTOR = ThreadPoolExecutor(max_workers=ARCHIVE_WORKERS)


def IsLossy(dicom, tags):
    return (
        dicom.GetInstanceTransferSyntaxUid() in LOSSY_TRANSFER_SYNTAXES
        or tags.get('LossyImageCompression') == '01'
    )


def IsDerived(tags):
    imageType = tags.get('ImageType')
    if isinstance(imageType, list):
        return bool(imageType) and imageType[0] == 'DERIVED'
    return str(imageType or '').split('\\')[0] == 'DERIVED'


def BuildDeterministicSopInstanceUid(sourceSopInstanceUid):
    profile = '|'.join((
        sourceSopInstanceUid,
        TARGET_TRANSFER_SYNTAX,
        str(LOSSY_QUALITY),
        str(COMPRESSION_PROFILE_VERSION),
    ))
    return f'2.25.{uuid.uuid5(uuid.NAMESPACE_URL, profile).int}'


def BuildDerivedImageType(imageType):
    if imageType is None:
        return ['DERIVED', 'PRIMARY']

    values = (
        list(imageType)
        if not isinstance(imageType, str)
        else imageType.split('\\')
    )
    if not values:
        return ['DERIVED', 'PRIMARY']

    values[0] = 'DERIVED'
    return values


def BuildArchivePathPrefix(sourceTags):
    identifiers = (
        sourceTags.get('StudyInstanceUID'),
        sourceTags.get('SeriesInstanceUID'),
        sourceTags.get('SOPInstanceUID'),
    )
    if not all(identifiers):
        raise ValueError('study, series, and SOP instance UIDs are required')

    return '/'.join((ARCHIVE_PREFIX, *identifiers))


def BuildArchiveKey(sourceTags, digest):
    return f'{BuildArchivePathPrefix(sourceTags)}/{digest}.dcm'


def BuildArchiveManifestKey(sourceTags):
    return f'{BuildArchivePathPrefix(sourceTags)}/manifest.json'


def ConfirmArchiveManifest(sourceTags, digest, archiveKey):
    manifestKey = BuildArchiveManifestKey(sourceTags)
    manifestData = {
        'archive_key': archiveKey,
        'series_instance_uid': sourceTags['SeriesInstanceUID'],
        'sha256': digest,
        'sop_instance_uid': sourceTags['SOPInstanceUID'],
        'study_instance_uid': sourceTags['StudyInstanceUID'],
    }
    manifest = json.dumps(
        manifestData,
        separators=(',', ':'),
        sort_keys=True,
    ).encode('utf-8')
    manifestChecksum = base64.b64encode(
        hashlib.sha256(manifest).digest()
    ).decode('ascii')

    try:
        response = ARCHIVE_CLIENT.put_object(
            Bucket=ARCHIVE_BUCKET,
            Key=manifestKey,
            Body=manifest,
            ContentLength=len(manifest),
            ContentType='application/json',
            ChecksumSHA256=manifestChecksum,
            IfNoneMatch='*',
            ServerSideEncryption='AES256',
        )
        if response.get('ChecksumSHA256') != manifestChecksum:
            raise RuntimeError('S3 did not confirm the archive manifest checksum')
    except ClientError as error:
        code = error.response.get('Error', {}).get('Code')
        status = error.response.get('ResponseMetadata', {}).get(
            'HTTPStatusCode'
        )
        if code not in ('PreconditionFailed', '412') and status != 412:
            raise

        existing = ARCHIVE_CLIENT.get_object(
            Bucket=ARCHIVE_BUCKET,
            Key=manifestKey,
        )
        existingManifest = json.loads(existing['Body'].read())
        if existingManifest != manifestData:
            raise RuntimeError(
                'archive manifest conflicts with incoming DICOM bytes; '
                f'lossless copy preserved at {archiveKey}'
            )


def ArchiveOriginal(receivedDicom, sourceTags):
    digest = hashlib.sha256(receivedDicom).hexdigest()
    checksum = base64.b64encode(bytes.fromhex(digest)).decode('ascii')
    key = BuildArchiveKey(sourceTags, digest)

    try:
        response = ARCHIVE_CLIENT.put_object(
            Bucket=ARCHIVE_BUCKET,
            Key=key,
            Body=receivedDicom,
            ContentLength=len(receivedDicom),
            ContentType='application/dicom',
            ChecksumSHA256=checksum,
            IfNoneMatch='*',
            Metadata={
                'sha256': digest,
                'study-instance-uid': sourceTags['StudyInstanceUID'],
                'series-instance-uid': sourceTags['SeriesInstanceUID'],
                'sop-instance-uid': sourceTags['SOPInstanceUID'],
            },
            ServerSideEncryption='AES256',
        )
        if response.get('ChecksumSHA256') != checksum:
            raise RuntimeError('S3 did not confirm the lossless archive checksum')
    except ClientError as error:
        code = error.response.get('Error', {}).get('Code')
        status = error.response.get('ResponseMetadata', {}).get(
            'HTTPStatusCode'
        )
        if code not in ('PreconditionFailed', '412') and status != 412:
            raise

        existing = ARCHIVE_CLIENT.head_object(
            Bucket=ARCHIVE_BUCKET,
            Key=key,
        )
        if (
            existing.get('ContentLength') != len(receivedDicom)
            or existing.get('Metadata', {}).get('sha256') != digest
        ):
            raise RuntimeError('existing lossless archive object did not match')

    ConfirmArchiveManifest(sourceTags, digest, key)
    return key


def PrepareTranscodedDicom(transcodedBytes, sourceSopInstanceUid):
    dataset = dcmread(BytesIO(transcodedBytes))
    generatedSopInstanceUid = str(dataset.SOPInstanceUID)
    if generatedSopInstanceUid == sourceSopInstanceUid:
        raise ValueError('lossy transcoding did not generate a new SOPInstanceUID')

    deterministicSopInstanceUid = BuildDeterministicSopInstanceUid(
        sourceSopInstanceUid
    )
    dataset.SOPInstanceUID = deterministicSopInstanceUid

    if not getattr(dataset, 'file_meta', None):
        raise ValueError('transcoded DICOM is missing file metadata')
    dataset.file_meta.MediaStorageSOPInstanceUID = deterministicSopInstanceUid

    dataset.ImageType = BuildDerivedImageType(
        getattr(dataset, 'ImageType', None)
    )
    dataset.LossyImageCompression = '01'
    dataset.LossyImageCompressionMethod = 'ISO_10918_1'
    dataset.DerivationDescription = (
        f'Lossy JPEG compression at quality {LOSSY_QUALITY}'
    )

    sourceReference = Dataset()
    sourceReference.ReferencedSOPClassUID = dataset.SOPClassUID
    sourceReference.ReferencedSOPInstanceUID = sourceSopInstanceUid
    dataset.SourceImageSequence = [sourceReference]

    output = BytesIO()
    dcmwrite(output, dataset, write_like_original=False)
    return output.getvalue(), deterministicSopInstanceUid


def ValidateTranscodedDicom(
    source,
    sourceTags,
    transcoded,
    expectedSopInstanceUid,
):
    transcodedTags = GetTags(transcoded)

    for tag in IDENTITY_TAGS:
        if (
            not sourceTags.get(tag)
            or transcodedTags.get(tag) != sourceTags.get(tag)
        ):
            raise ValueError(f'{tag} changed during transcoding')

    if transcodedTags.get('SOPInstanceUID') != expectedSopInstanceUid:
        raise ValueError('unexpected SOPInstanceUID after transcoding')

    if transcoded.GetInstanceTransferSyntaxUid() != TARGET_TRANSFER_SYNTAX:
        raise ValueError('unexpected transfer syntax after transcoding')

    if transcoded.GetInstanceFramesCount() != source.GetInstanceFramesCount():
        raise ValueError('frame count changed during transcoding')

    if transcodedTags.get('LossyImageCompression') != '01':
        raise ValueError('lossy compression metadata is missing')

    if transcodedTags.get('LossyImageCompressionMethod') != 'ISO_10918_1':
        raise ValueError('lossy compression method metadata is missing')

    if not IsDerived(transcodedTags):
        raise ValueError('derived image metadata is missing')


def ReceivedInstanceCallback(receivedDicom, origin):
    archiveFuture = None
    archiveWaitStarted = False
    try:
        source = orthanc.CreateDicomInstance(receivedDicom)
        sourceTags = GetTags(source)

        if sourceTags.get('Modality') != 'US':
            return orthanc.ReceivedInstanceAction.KEEP_AS_IS, None

        if source.GetInstanceFramesCount() <= 1 or IsLossy(source, sourceTags):
            return orthanc.ReceivedInstanceAction.KEEP_AS_IS, None

        sourceSopInstanceUid = sourceTags.get('SOPInstanceUID')
        if not sourceSopInstanceUid:
            raise ValueError('SOPInstanceUID is missing')

        archiveFuture = ARCHIVE_EXECUTOR.submit(
            ArchiveOriginal,
            receivedDicom,
            sourceTags,
        )
        transcoded = orthanc.TranscodeDicomInstance(
            receivedDicom,
            TARGET_TRANSFER_SYNTAX,
        )
        transcodedBytes, deterministicSopInstanceUid = PrepareTranscodedDicom(
            transcoded.SerializeDicomInstance(),
            sourceSopInstanceUid,
        )
        validated = orthanc.CreateDicomInstance(transcodedBytes)
        ValidateTranscodedDicom(
            source,
            sourceTags,
            validated,
            deterministicSopInstanceUid,
        )
        archiveWaitStarted = True
        archiveKey = archiveFuture.result(timeout=ARCHIVE_TIMEOUT_SECONDS)

        orthanc.LogInfo(
            f'Transcoded multiframe US to JPEG Lossy before storage: '
            f'{len(receivedDicom)} bytes to {len(transcodedBytes)} bytes; '
            f'lossless archive {archiveKey}'
        )
        return orthanc.ReceivedInstanceAction.MODIFY, transcodedBytes
    except Exception as e:
        if archiveFuture is not None and not archiveWaitStarted:
            try:
                archiveFuture.result(timeout=ARCHIVE_TIMEOUT_SECONDS)
            except Exception:
                pass
        orthanc.LogError(
            f'Keeping original DICOM after US compression/archive failed: {e}'
        )
        return orthanc.ReceivedInstanceAction.KEEP_AS_IS, None


# Install requirements-compress-us-to-lossy.txt, configure
# LOSSLESS_ARCHIVE_BUCKET, and use Orthanc Python plugin 4.0 or newer. The
# deterministic derived SOP UID prevents retransmission duplicates.
try:
    ValidateConfiguration()
    ConfigureArchiveClient()
    orthanc.RegisterReceivedInstanceCallback(ReceivedInstanceCallback)
except Exception as e:
    orthanc.LogError(f'US compression plugin disabled: {e}')
