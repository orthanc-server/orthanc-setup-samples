import orthanc

# this sample demonstrates how to retry jobs in python.
# this should be improved with the use of message queues
# e.g to resubmit jobs after a delay...


def OnChange(changeType, level, resource):

  if changeType == orthanc.ChangeType.JOB_SUCCESS:

    orthanc.LogInfo(f"job {resource} has succeeded")

  elif changeType == orthanc.ChangeType.JOB_FAILURE:

    orthanc.LogWarning(f"job {resource} has failed, retrying")
    orthanc.RestApiPost(f"/jobs/{resource}/resubmit", "")

  elif changeType == orthanc.ChangeType.JOB_SUBMITTED:

    orthanc.LogInfo(f"job {resource} has been submitted")


orthanc.RegisterOnChangeCallback(OnChange)
