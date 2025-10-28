import orthanc
import json
import pprint, os
import dataclasses

###
# This plugins filters out some instances when
# - a C-Move is received
# - a C-Store is performed
#
# The filter applies only on some AET.
# The filter criteria is the SOPClassUID
###

# Here is the list of the (begining of) SOPClassUID's to filter out
EXCLUDED_SOP_CLASSES = [
    "1.2.840.10008.5.1.4.1.1.104.1"
]

# Here is the list of the AET of the modalities to apply the filter to.
AET_TO_APPLY_THE_FILTER_TO = [
    "MODALITY"
]

def GetOrthancAliasFromAET(AET):
    '''
    The initial DICOM query will contain an AET, but we need the Orthanc alias to perform the C-Store
    :param AET: AET to send the resource to
    :return: the Orthanc alias corresponding to the AET
    '''
    modalities = json.loads(orthanc.RestApiGet('/modalities?expand'))

    for modality, modalityDetails in modalities.items():
        if modalityDetails["AET"] == AET:
            return modality

    raise Exception('It seems that the modality issuing the original DICOM query is not registered in the config!')


class MoveDriver:

    def __init__(self, request) -> None:
        self.request = request
        self.instances_to_move = []
        self.instance_counter = 0
        self.memory = [0] * 10000000

        if verbose_enabled:
            pprint.pprint("original C-move query:")
            pprint.pprint(request)

        if request["SourceAET"] in {None, ''}:
            raise Exception('The DICOM query does not contain a value for the SourceAET, unable to process it!')

        if request["Level"] in {None, ''}:
            raise Exception('The DICOM query does not contain a value for the tag Level, unable to process it!')

        self.level = request["Level"]
        self.remote_server = request["SourceAET"]

        if request["StudyInstanceUID"] in {None, ''}:
            raise Exception('The DICOM query does not contain a value for the StudyInstanceUID, unable to process it!')
        else:
            # A C-move query can contain 2 (or more) values in the 'StudyInstanceUID' tag, separated by '\'
            # So, we have to handle all of them separately:
            self.study_instance_uid_list = request["StudyInstanceUID"].split("\\")

        if self.level in {"SERIES", "IMAGE", "INSTANCE"}:
            if request["SeriesInstanceUID"] in {None, ''}:
                raise Exception('The DICOM query does not contain a value for the SeriesInstanceUID, unable to process it!')
            else:
                self.series_instance_uid = request["SeriesInstanceUID"]

            if self.level in {"IMAGE", "INSTANCE"}:

                if request["SOPInstanceUID"] in {None, ''}:
                    raise Exception('The DICOM query does not contain a value for the SOPInstanceUID, unable to process it!')
                else:
                    sop_instance_uid = request["SOPInstanceUID"]
                    self.instance_uid = sop_instance_uid

        self.target_aet = None
        if request["TargetAET"] in {None, ''}:
            self.target_aet = request["OriginatorAET"]
        else:
            self.target_aet = request["TargetAET"]

        self.target_modality_alias = GetOrthancAliasFromAET(self.target_aet)

    # get the instances
    def get_instances_list(self):
        request = self.request

        for study_instance_uid in self.study_instance_uid_list:

            # get the list of all instances
            
            if self.level == "STUDY":
                lookup = json.loads(orthanc.RestApiPostAfterPlugins('/tools/lookup', study_instance_uid))

                instances = json.loads(orthanc.RestApiGetAfterPlugins('/studies/{0}/instances'.format(lookup[0]['ID'])))
    
            elif self.level == "SERIES":
                lookup = json.loads(orthanc.RestApiPostAfterPlugins('/tools/lookup', self.series_instance_uid))

                instances = json.loads(orthanc.RestApiGetAfterPlugins('/series/{0}/instances'.format(orthanc_id)))
            elif self.level in {"IMAGE", "INSTANCE"}:
                lookup = json.loads(orthanc.RestApiPostAfterPlugins('/tools/lookup', self.instance_uid))

                self.instances_to_move = [lookup[0]['ID']]
                return

            for instance in instances:
                orthanc_id = instance["ID"]
                self.instances_to_move.append(orthanc_id)


    def forward_instance(self, orthanc_id: str):

        # get SOPClassUID        
        sop_class_uid = json.loads(orthanc.RestApiGet('/instances/{0}/tags'.format(orthanc_id)))["0008,0016"]["Value"]

        if self.target_aet in AET_TO_APPLY_THE_FILTER_TO and sop_class_uid.startswith(tuple(EXCLUDED_SOP_CLASSES)):
            return

        # C-store
        orthanc.RestApiPost('/modalities/{0}/store'.format(self.target_modality_alias), json.dumps({
            "Resources": [orthanc_id]
        }))
        

    def cleanup(self):
        # we may have some ids remaining in the list, we tranfer all of them here
        for instance in self.instances_to_move:
            self.forward_instance(instance)
        self.instances_to_move.clear()
        

def CreateMoveCallback(**request):
    # simply create the move driver object now and return it to Orthanc
    orthanc.LogInfo("CreateMoveCallback")
    # pprint.pprint(request)

    driver = MoveDriver(request=request)

    return driver

def GetMoveSizeCallback(driver: MoveDriver):
    # query the remote server to list and count the instances to retrieve
    orthanc.LogInfo("GetMoveSizeCallback")

    driver.get_instances_list()

    return len(driver.instances_to_move)
    

def ApplyMoveCallback(driver: MoveDriver):
    orthanc.LogInfo("ApplyMoveCallback")

    # let's get the first instance id (from the list containing all of them)
    instance_id = driver.instances_to_move[0]

    driver.forward_instance(instance_id)

    # let's remove the id from the list
    driver.instances_to_move.remove(instance_id)

    return 0 # 0 is success, you should raise an exception in case of errors

def FreeMoveCallback(driver):
    # free the resources that have been allocated by the move driver
    orthanc.LogInfo("FreeMoveCallback")

    driver.cleanup()

def OnStore(output, uri, **request):

    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')
    
    else:
        query = json.loads(request['body'])
        query["Permissive"] = True

    answer = orthanc.RestApiPost(uri, json.dumps(query))

    output.AnswerBuffer(answer, 'application/json')


orthanc.RegisterMoveCallback2(CreateMoveCallback, GetMoveSizeCallback, ApplyMoveCallback, FreeMoveCallback)
orthanc.RegisterRestCallback('/modalities/(.*)/store', OnStore)


if os.environ.get('VERBOSE_ENABLED') in ["true", "True", True]:
    verbose_enabled = True
