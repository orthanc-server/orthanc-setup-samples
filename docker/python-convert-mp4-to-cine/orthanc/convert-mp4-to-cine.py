import orthanc
import pprint
import os
import io
import base64
import json
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid, JPEGBaseline8Bit
from pydicom.encaps import encapsulate, encapsulate_extended


from decord import VideoReader
from decord import cpu
from PIL import Image


def convert_video_to_cine(output, uri, **request):

    video_file_content = io.BytesIO(request['body'])
    video_frames = VideoReader(video_file_content)

    study_instance_uid = orthanc.RestApiGet("/tools/generate-uid?level=study").decode('utf-8')
    series_instance_uid = orthanc.RestApiGet("/tools/generate-uid?level=series").decode('utf-8')

    instance_number = 1
    compressed_frames = []
    for raw_frame in video_frames:
        pil_image = Image.fromarray(raw_frame.asnumpy())
        jpeg_buffer = io.BytesIO()
        pil_image.save(jpeg_buffer, format='JPEG', subsampling=0, quality=95)

        jpeg_buffer.seek(0)
        compressed_frames.append(jpeg_buffer.read())

    ds = Dataset()
    ds.Rows = pil_image.height
    ds.Columns = pil_image.width
    ds.Modality = "XC"
    ds.SeriesInstanceUID = series_instance_uid
    ds.StudyInstanceUID = study_instance_uid
    ds.StudyDescription = "VIDEO to DICOM test study"
    ds.SeriesDescription = "VIDEO to DICOM test series"
    ds.SOPInstanceUID = generate_uid()
    ds.SamplesPerPixel = 3  # RGB
    ds.PhotometricInterpretation = "YBR"  #YBR because we are compressing to jpeg !
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.SeriesNumber = 100
    ds.InstanceNumber = instance_number
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.NumberOfFrames = len(compressed_frames)
    ds.SopClassUID = "1.2.840.10008.5.1.4.1.1.7" # secondary capture
    ds.PixelData = encapsulate(compressed_frames)  # for raw image: frame.asnumpy().tobytes()
    ds.file_meta = Dataset()
    ds.file_meta.TransferSyntaxUID = JPEGBaseline8Bit
    
    dicom_buffer = io.BytesIO()
    ds.save_as(dicom_buffer)
    dicom_buffer.seek(0)

    ret = json.loads(orthanc.RestApiPost("/instances", dicom_buffer.read()))
    pprint.pprint(ret)


    # pprint.pprint(request)
    output.AnswerBuffer(f"{len(compressed_frames)}\n", 'text/plain')

orthanc.RegisterRestCallback('/video-to-cine', convert_video_to_cine)

