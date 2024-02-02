import io
import orthanc
import sys
import pprint

# uncomment to show the python path
#pprint.pprint(sys.path)

import pydicom
from doc import InspectOrthancModule


# uncomment to show the Orthanc Module functions/classes/enums
# InspectOrthancModule()



def OnRestPydicom(output, uri, **request):
    if request['method'] == 'GET':
        # Retrieve the instance ID from the regular expression (*)
        instanceId = request['groups'][0]
        # Get the content of the DICOM file
        f = orthanc.GetDicomForInstance(instanceId)
        # Parse it using pydicom
        dicom = pydicom.dcmread(io.BytesIO(f))
        # Return a string representation the dataset to the caller
        output.AnswerBuffer(str(dicom), 'text/plain')
    else:
        output.SendMethodNotAllowed('GET')


# add two rest callback
orthanc.RegisterRestCallback('/pydicom/(.*)', OnRestPydicom)  # (*)


# add a "show-metadata" button in the Orthanc Explorer
# add a "show-pydicom" button in the Orthanc Explorer
with open("/python/extend-explorer.js", "r") as f:
    orthanc.ExtendOrthancExplorer(f.read())

