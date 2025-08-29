import orthanc
import pprint
import json
import re
import zipfile
import io
from PIL import Image, ImageDraw, ImageFont


# This plugin adds an API route to retrieve a zip file with a JPEG preview of each instance/series of a study.
# If setting preview-level=series (default), the plugin will only take the preview of the middle instance of each series.
# If setting preview-level=instances, the plugin will the preview of each instance of each study.
# Example:
# http://localhost:80442/studies/595df1a1-74fe920a-4b9e3509-826f17a3-762a2dc3/download-as-jpeg-archive?preview-level=series&filename=toto.zip
# http://localhost:80442/studies/595df1a1-74fe920a-4b9e3509-826f17a3-762a2dc3/download-as-jpeg-archive?preview-level=instance
#
# It also allows to burn some DICOM tags values into the jpeg.
# Some templates have to be defined:

top_left_template="""PatientName: {PatientName}
PatientID: {PatientID}
Birth: {PatientBirthDate}
"""

top_right_template="""InstitutionName: {InstitutionName}
StudyDate: {StudyDate}
StudyTime: {StudyTime}
"""

# Helper method to replace '{tagName}' by their value in a string
# {UUID} is replaced by the resource_id
def replace_tags_with_values(template, tags, resource_id):
    
    def replace_match(match):
        key = match.group(1)
        return tags.get(key, match.group(0))

    replaced = re.sub(r'\{(\w+)\}', replace_match, template)
    if resource_id is not None:
        replaced = replaced.replace('{UUID}', resource_id)
    return replaced

# Burns some DICOM tags into the jpeg according to the templates.
def burn_study_info(jpeg_content, resource_tags):
    image = Image.open(io.BytesIO(jpeg_content))
    draw = ImageDraw.Draw(image)

    # Here is an arbitrary choice, the font size will be 2% of the full height of the image
    font_size = image.size[1] * 0.02
    font = ImageFont.load_default(size=font_size)

    # colors mgmt depends on the jpeg "color space"
    if image.mode == "L":  # grayscale case
        fill = 255
        stroke_fill = 0
    else:  # RGB case
        fill = (255, 255, 255)
        stroke_fill = (0, 0, 0)

    # top left string to burn
    if top_left_template is not None:
        top_left_string = replace_tags_with_values(template=top_left_template, tags=resource_tags,
                                               resource_id=None)
        position = (0, 0)
        draw.text(position, top_left_string, fill=fill, stroke_width=0, stroke_fill=stroke_fill, font=font)

    # top right string to burn
    if top_right_template is not None:
        top_right_string = replace_tags_with_values(template=top_right_template, tags=resource_tags,
                                                    resource_id=None)
        bbox = draw.textbbox((0, 0), top_right_string, font=font)
        position = (image.size[0] - bbox[2], 0)
        draw.text(position,
                  top_right_string,
                  fill=fill,  # text color (white)
                  stroke_width=0,  # thickness of border
                  stroke_fill=stroke_fill,
                  font=font,
                  align="right")

    image_bytes = io.BytesIO()
    image.save(image_bytes, format='JPEG')

    return image_bytes.getvalue()


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

            resource_tags = {**study_tags, **instance['MainDicomTags']}

            try:
                jpeg_content = orthanc.RestApiGet(f'/instances/{instance["ID"]}/preview')

                if top_left_template is not None or top_right_template is not None:
                    jpeg_content = burn_study_info(jpeg_content=jpeg_content, resource_tags=resource_tags)

            except Exception as e:
                # here is an instance which can't be previewed (pdf, video,...), let's skip it
                continue

            # build the filename of the jpeg in the zip
            if 'RequestedTags' in instance:
                resource_tags.update(instance['RequestedTags'])
            jpg_filename = replace_tags_with_values(template=jpeg_filename_template, tags=resource_tags, resource_id=instance["ID"])
            
            zf.writestr(jpg_filename, jpeg_content)

    output.SetHttpHeader('Content-Disposition', f'filename={zip_filename}')
    output.AnswerBuffer(mem_zip.getvalue(), 'application/zip')
   

orthanc.RegisterRestCallback('/studies/(.*)/download-as-jpeg-archive', OnGetJpegArchive)