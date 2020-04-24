import io
import orthanc
import pprint
import json
import multiprocessing
import signal
from doc import InspectOrthancModule
from sanitizer import Sanitizer

# uncomment to show the Orthanc Module functions/classes/enums
# InspectOrthancModule()

# the Sanitizer will run in another process and have 4 workers thread
sanitizer = Sanitizer(4)


def OnChange(changeType, level, resource):

  # at startup, we should detect all instances that are currently in
  # Orthanc and we shall queue them "for processing"
  if changeType == orthanc.ChangeType.ORTHANC_STARTED:

    allInstancesIds = json.loads(orthanc.RestApiGet("/instances"))
    for instanceId in allInstancesIds:
      sanitizer.push(instanceId)

    sanitizer.start()

  elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:

    sanitizer.stop()

  # everytime a new instance is received, we shall queue it "for processing"
  elif changeType == orthanc.ChangeType.NEW_INSTANCE:

    sanitizer.push(resource)

orthanc.RegisterOnChangeCallback(OnChange)
