import json
import pprint
import os
import base64
import orthanc

# this plugin adds the username as a label to the study
def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_STUDY:
        orthanc.LogInfo(f"A new study has been received {resource}")
        
        # bypass the plugins, including the auth-plugin -> this plugin has access to all studies
        study_instances = json.loads(orthanc.RestApiGet(f"/studies/{resource}/instances?expand=false"))
        instance_metadata = json.loads(orthanc.RestApiGet(f"/instances/{study_instances[0]}/metadata?expand"))
        pprint.pprint(instance_metadata)

        if 'HttpUsername' in instance_metadata:
            user = instance_metadata['HttpUsername']
            orthanc.LogInfo(f"The study has been uploaded by '{user}' and will be labeled accordingly")
            orthanc.RestApiPut(f"/studies/{resource}/labels/{user}", "")


orthanc.RegisterOnChangeCallback(OnChange)


