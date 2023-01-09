# sample code to attach a PDF to an existing study using the Orthanc Rest API

import requests
import base64

# read PDF from disk and attach it to an existing study
with open("/tmp/sample-pdf.pdf", "rb") as f:
    pdf_content = f.read()

study_id = "013f5776-2df7479a-d0969e92-b5a5dc94-aef7e4a2"
orthanc_url = "http://192.168.0.10:8042"

r = requests.post(
    url=f"{orthanc_url}/tools/create-dicom",
    json={
        "Parent" : study_id,
        "Tags" : {
            "Modality" : "OT",
            "SeriesDescription" : "Sample protocol"
        },
        "Content": "data:application/pdf;base64," + base64.b64encode(pdf_content).decode('utf-8')
    }
)

if r.status_code == 200:
    instance_id = r.json()['ID']
    print("Created new instance " + instance_id)

    # read back PDF from Orthanc

    r = requests.get(
        url=f"{orthanc_url}/instances/{instance_id}/pdf",
    )

    if r.status_code == 200:
        print("Saving PDF")
        with open("/tmp/sample-pdf-readback.pdf", "wb") as f:
            f.write(r.content)
