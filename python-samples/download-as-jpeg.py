import orthanc
import pprint
import json
import re
import zipfile
import io

# This plugin adds an API route to retrieve a zip file with a JPEG preview of each instance/series of a study.
# If setting preview-level=series (default), the plugin will only take the preview of the middle instance of each series.
# If setting preview-level=instances, the plugin will the preview of each instance of each study.
# Example:
# http://localhost:80442/studies/595df1a1-74fe920a-4b9e3509-826f17a3-762a2dc3/download-as-jpeg-archive?preview-level=series&filename=toto.zip
# http://localhost:80442/studies/595df1a1-74fe920a-4b9e3509-826f17a3-762a2dc3/download-as-jpeg-archive?preview-level=instance

# Helper method to replace '{tagName}' by their value in a string
# {UUID} is replaced by the resource_id
def replace_tags_with_values(template, tags, resource_id):
    
    def replace_match(match):
        key = match.group(1)
        return tags.get(key, match.group(0))

    replaced = re.sub(r'\{(\w+)\}', replace_match, template)
    replaced = replaced.replace('{UUID}', resource_id)
    return replaced


# Orthanc Rest API callback
def OnGetJpegArchive(output, uri, **request):

    if request['method'] != 'GET':
        output.SendMethodNotAllowed('GET')

    study_id = request['groups'][0]

    # default values
    preview_level = 'series'
    zip_filename = "{PatientID}-{PatientName}-{StudyDate}-{StudyDescription}-jpeg.zip"

    if 'get' in request:
        if 'preview-level' in request['get']:
            preview_level = request['get']['preview-level']
        if 'filename' in request['get']:
            zip_filename = request['get']['filename']

    if preview_level not in ['series', 'instance']:
        output.SendHttpStatus(400)

    # pprint.pprint(request)
    # print(f"Accessing JPEG archive for study: {study_id}")

    # build the zip filename
    study_info = json.loads(orthanc.RestApiGet(f'/studies/{study_id}'))
    study_tags = {**study_info['MainDicomTags'], **study_info['PatientMainDicomTags']}
    zip_filename = replace_tags_with_values(template=zip_filename, tags=study_tags, resource_id=study_id)

    # list the instances
    instances = []
    
    if preview_level == 'series':
        series_ids = json.loads(orthanc.RestApiGet(f'/studies/{study_id}/series?expand=false'))
        
        for series_id in series_ids:
            # for each series, get only the middle instance
            payload = {
                'Query': {},
                'Level': 'Instance',
                'ParentSeries': series_id,
                'RequestedTags': ['SeriesDate', 'SeriesDescription', 'SeriesNumber'],
                'OrderBy': [{
                    'Type': 'Metadata',
                    'Key': 'IndexInSeries',
                    'Direction': 'ASC'
                }],
                'ResponseContent': ['RequestedTags', 'MainDicomTags']
            }
            series_instances = json.loads(orthanc.RestApiPost('/tools/find', json.dumps(payload)))
            # pprint.pprint(series_instances)            
            middle_instance = series_instances[int(len(series_instances)/2)]
            instances.append(middle_instance)

        # pprint.pprint(instances)
        jpeg_filename_template = "{SeriesNumber}-{SeriesDescription}.jpg"
    elif preview_level == 'instance':
        instances = json.loads(orthanc.RestApiGet(f'/studies/{study_id}/instances?expand=true&requestedTags=SeriesDate;SeriesDescription;SeriesNumber'))
        jpeg_filename_template = "{SeriesNumber}-{SeriesDescription}-{InstanceNumber}.jpg"

    # build the zip
    mem_zip = io.BytesIO()

    with zipfile.ZipFile(mem_zip, mode="w",compression=zipfile.ZIP_DEFLATED) as zf:

        for instance in instances:
            # print(f'downloading /preview for {instance["ID"]}')
            # pprint.pprint(instance)

            try:
                jpeg_content = orthanc.RestApiGet(f'/instances/{instance["ID"]}/preview')
            except Exception as e:
                # here is probably an instance which can't be previewed (pdf, video,...), let's skip it
                # TODO: catch only 415 http errors (bug in Python wrapper?)
                continue

            # build the filename of the jpeg in the zip
            resource_tags = {**study_tags, **instance['MainDicomTags']}
            if 'RequestedTags' in instance:
                resource_tags.update(instance['RequestedTags'])
            jpg_filename = replace_tags_with_values(template=jpeg_filename_template, tags=resource_tags, resource_id=instance["ID"])
            
            zf.writestr(jpg_filename, jpeg_content)

    output.SetHttpHeader('Content-Disposition', f'filename={zip_filename}')
    output.AnswerBuffer(mem_zip.getvalue(), 'application/zip')
   

orthanc.RegisterRestCallback('/studies/(.*)/download-as-jpeg-archive', OnGetJpegArchive)