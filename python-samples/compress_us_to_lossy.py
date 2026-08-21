import orthanc
import json

# this script compresses US images to lossy JPEG to reduce their sizes.
# Prerequisites:
# - You must have "OverwriteInstances" set to true (or to "Always"/"IfChanged" if you are using Orthanc 1.13.0+)
# - If you have not configured an "IngestTranscoding", this script will work fine.
# - If you have configured an "IngestTranscoding", this script will
#   work only if you have also set "IngestTranscodingOfCompressed" to false to aovid
#   re-applying IngestTranscoding to the modified instance.


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

        # download a transcoded instance and make sur to keep the SOPInstanceUID unchanged
        transcoded_instance = orthanc.RestApiPost(f'/instances/{instanceId}/modify', json.dumps({
            "Transcode": "1.2.840.10008.1.2.4.50", 
            "Replace": {"SOPInstanceUID": tags.get('SOPInstanceUID') }, 
            "Force": True,
            "LossyQuality": 70
        }))

        # re-upload the instance.
        upload_response = json.loads(orthanc.RestApiPost('/instances', transcoded_instance))

        if upload_response.get('ID') != instanceId:
            orthanc.LogError(f'The transcoded instance {upload_response.get("ID")} does not have the same ID as the source {instanceId}')
            return

        orthanc.LogInfo(f"Transcoded US image to JPEG Lossy: {instanceId}.  New size = {len(transcoded_instance)} vs {dicom.GetInstanceSize()}")

orthanc.RegisterOnStoredInstanceCallback(OnStoredInstance)
