import json

import orthanc


# Requires Orthanc Python plugin 4.0 or newer.
TARGET_TRANSFER_SYNTAX = '1.2.840.10008.1.2.4.50'
LOSSY_QUALITY = 70
LOSSY_TRANSFER_SYNTAXES = {
    '1.2.840.10008.1.2.4.50',
    '1.2.840.10008.1.2.4.51',
    '1.2.840.10008.1.2.4.81',
}
IDENTITY_TAGS = (
    'PatientID',
    'StudyInstanceUID',
    'SeriesInstanceUID',
)


def GetTags(dicom):
    return json.loads(dicom.GetInstanceSimplifiedJson())


def IsLossy(dicom, tags):
    return (
        dicom.GetInstanceTransferSyntaxUid() in LOSSY_TRANSFER_SYNTAXES
        or tags.get('LossyImageCompression') == '01'
    )


def ValidateConfiguration():
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


def ValidateTranscodedDicom(source, sourceTags, transcoded):
    transcodedTags = GetTags(transcoded)

    for tag in IDENTITY_TAGS:
        if not sourceTags.get(tag) or transcodedTags.get(tag) != sourceTags.get(tag):
            raise ValueError(f'{tag} changed during transcoding')

    sourceSopInstanceUid = sourceTags.get('SOPInstanceUID')
    transcodedSopInstanceUid = transcodedTags.get('SOPInstanceUID')
    if not sourceSopInstanceUid or not transcodedSopInstanceUid:
        raise ValueError('SOPInstanceUID is missing')
    if transcodedSopInstanceUid == sourceSopInstanceUid:
        raise ValueError('SOPInstanceUID did not change during lossy transcoding')

    if transcoded.GetInstanceTransferSyntaxUid() != TARGET_TRANSFER_SYNTAX:
        raise ValueError('unexpected transfer syntax after transcoding')

    if transcoded.GetInstanceFramesCount() != source.GetInstanceFramesCount():
        raise ValueError('frame count changed during transcoding')

    if transcodedTags.get('LossyImageCompression') != '01':
        raise ValueError('lossy compression metadata is missing')


def ReceivedInstanceCallback(receivedDicom, origin):
    try:
        source = orthanc.CreateDicomInstance(receivedDicom)
        sourceTags = GetTags(source)

        if sourceTags.get('Modality') != 'US':
            return orthanc.ReceivedInstanceAction.KEEP_AS_IS, None

        if source.GetInstanceFramesCount() <= 1 or IsLossy(source, sourceTags):
            return orthanc.ReceivedInstanceAction.KEEP_AS_IS, None

        transcoded = orthanc.TranscodeDicomInstance(
            receivedDicom,
            TARGET_TRANSFER_SYNTAX,
        )
        ValidateTranscodedDicom(source, sourceTags, transcoded)
        transcodedDicom = transcoded.SerializeDicomInstance()

        orthanc.LogInfo(
            f'Transcoded multiframe US to JPEG Lossy: '
            f'{len(receivedDicom)} bytes to {len(transcodedDicom)} bytes'
        )
        return orthanc.ReceivedInstanceAction.MODIFY, transcodedDicom
    except Exception as e:
        orthanc.LogError(f'Keeping original DICOM after US transcoding failed: {e}')
        return orthanc.ReceivedInstanceAction.KEEP_AS_IS, None


try:
    ValidateConfiguration()
    orthanc.RegisterReceivedInstanceCallback(ReceivedInstanceCallback)
except Exception as e:
    orthanc.LogError(f'US compression plugin disabled: {e}')
