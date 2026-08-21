import orthanc
import json

# this script compresses US images to lossy JPEG to reduce their sizes.
# Prerequisites:
# - You must have "OverwriteInstances" set to true (or to "Always"/"IfChanged" if you are using Orthanc 1.13.0+)
# - If you have not configured an "IngestTranscoding", this script will work fine.
# - If you have configured an "IngestTranscoding", this script will
#   work only if you have also set "IngestTranscodingOfCompressed" to false to avoid
#   re-applying IngestTranscoding to the modified instance.


def GetSopInstanceUid(dicomBytes):
    instance = orthanc.CreateDicomInstance(dicomBytes)
    tags = json.loads(instance.GetInstanceSimplifiedJson())
    return tags.get('SOPInstanceUID')


def OnStoredInstance(dicom, instanceId):
    tags = json.loads(dicom.GetInstanceSimplifiedJson())

    # only handle the US images
    if tags.get('Modality') == 'US':

        # optional: only compress the multiframe US images since these are the ones consuming more space
        if dicom.GetInstanceFramesCount() == '1':
            return

        transfer_syntax = dicom.GetInstanceTransferSyntaxUid()

        # don't transcode if it is already in lossy jpeg
        if transfer_syntax in ['1.2.840.10008.1.2.4.50', '1.2.840.10008.1.2.4.51']:
            return

        source_sop_instance_uid = tags.get('SOPInstanceUID')
        if not source_sop_instance_uid:
            orthanc.LogError(f'Cannot transcode {instanceId}: source SOPInstanceUID is missing')
            return

        # download a transcoded instance and request that the SOPInstanceUID remain unchanged
        transcoded_instance = orthanc.RestApiPost(f'/instances/{instanceId}/modify', json.dumps({
            "Transcode": "1.2.840.10008.1.2.4.50",
            "Replace": {"SOPInstanceUID": source_sop_instance_uid},
            "Force": True,
            "LossyQuality": 70
        }))

        transcoded_sop_instance_uid = GetSopInstanceUid(transcoded_instance)
        if transcoded_sop_instance_uid != source_sop_instance_uid:
            orthanc.LogError(
                f'Refusing to upload transcoded instance for {instanceId}: '
                f'SOPInstanceUID changed from {source_sop_instance_uid} '
                f'to {transcoded_sop_instance_uid}'
            )
            return

        # re-upload the instance
        upload_response = json.loads(orthanc.RestApiPost('/instances', transcoded_instance))

        if upload_response.get('ID') != instanceId:
            orthanc.LogError(f'The transcoded instance {upload_response.get("ID")} does not have the same ID as the source {instanceId}')
            return

        orthanc.LogInfo(f"Transcoded US image to JPEG Lossy: {instanceId}.  New size = {len(transcoded_instance)} vs {dicom.GetInstanceSize()}")


orthanc.RegisterOnStoredInstanceCallback(OnStoredInstance)
