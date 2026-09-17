import orthanc
import json

def update_custom_data(output, uri, **request):
    if request['method'] == 'POST':
        instance_id = request['groups'][0]

        attachment_uuid = json.loads(orthanc.RestApiGet(f'/instances/{instance_id}/attachments/dicom/info'))['Uuid']
        orthanc.SetAttachmentCustomData(attachment_uuid, b'dummy')

    output.AnswerBuffer('ok', 'text/plain')

orthanc.RegisterRestCallback('/instances/(.*)/update-custom-data', update_custom_data)