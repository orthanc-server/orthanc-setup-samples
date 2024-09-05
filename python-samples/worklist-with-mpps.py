# This script is a boilerplate script to implement a worklist server
# with MPPS support.  As of v 1.12.4, Orthanc does not support MPPS
# therefore, this script implements an independant worklist server
# with pydicom.

# This worklist server uses 2 configurations from the Orthanc configuration file:
# "MPPSAet": the AET of this worklist server
# "DicomPortMPPS": the port to be used (must be different from Orthanc DicomPort)

# The script assumes you have a DB with the scheduled exams available.
# This DB being user specific, the interface code with the DB is not included in the script.
# Check the TODO-DB placeholders.

# This script is implemented as an Orthanc python plugin.  Orthanc is
# only responsible for starting/stopping the worklist server and providing the configuration.

# test command:
# findscu -v -W  -k "PatientName=" -k "(0040,0100)[0].Modality=MR" -k "(0040,0100)[0].ScheduledProcedureStepStartDate=20240101" localhost 4243

from pydicom.dataset import Dataset, FileDataset
import datetime
import json
import orthanc
import pynetdicom

from io import BytesIO
from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityPerformedProcedureStep
from pynetdicom.sop_class import ModalityWorklistInformationFind
from pynetdicom.sop_class import Verification
from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian, ExplicitVRBigEndian, generate_uid

worklist_server = None

managed_instances = {}

# TODO-DB: connect to your DB

def handle_find(event):
    """Handle a C-FIND request event."""       
    try:        
        ds = event.identifier        
        dsArray = find_worklist(ds)

        # Import stored SOP Instances        
        instances = []   
        for instance in dsArray:
            # Check if C-CANCEL has been received
            if event.is_cancelled:
                yield (0xFE00, None)
                return
            # Pending
            yield (0xFF00, instance)             
        # Indicate that no more data is available
        yield 0x0000, None  # Success status, no more datasets
    except Exception as e:
        s = str(e)
        orthanc.LogWarning("Error occured: %s" % s)    


# Implement the evt.EVT_N_CREATE handler
def handle_create(event):
    
    # Create a Modality Performed Procedure Step SOP Class Instance
    #   DICOM Standard, Part 3, Annex B.17
    ds = Dataset()
    try:
        # MPPS' N-CREATE request must have an *Affected SOP Instance UID*
        req = event.request
        #identifier = event.identifier
        if req.AffectedSOPInstanceUID is None:
            # Failed - invalid attribute value
            return 0x0106, None

        # Can't create a duplicate SOP Instance
        if req.AffectedSOPInstanceUID in managed_instances:
            # Failed - duplicate SOP Instance
            return 0x0111, None

        # The N-CREATE request's *Attribute List* dataset
        attr_list = event.attribute_list

        # Performed Procedure Step Status must be 'IN PROGRESS'
        if "PerformedProcedureStepStatus" not in attr_list:
            # Failed - missing attribute
            return 0x0120, None
        
        if attr_list.PerformedProcedureStepStatus.upper() != 'IN PROGRESS':
            return 0x0106, None

        # Skip other tests...

        # Add the SOP Common module elements (Annex C.12.1)
        ds.SOPClassUID = ModalityPerformedProcedureStep
        ds.SOPInstanceUID = req.AffectedSOPInstanceUID

        # Update with the requested attributes
        ds.update(attr_list)

        # Add the dataset to the managed SOP Instances
        managed_instances[ds.SOPInstanceUID] = ds

        
        modality = attr_list.Modality
        accession_number = attr_list.ScheduledStepAttributesSequence[0].AccessionNumber
        study_instance_uid =  attr_list.ScheduledStepAttributesSequence[0].StudyInstanceUID
        
        # TODO-DB: update your DB to record that this study acquisition has been started

    except Exception as e:
        s = str(e)
        orthanc.LogWarning("Error occured: %s" % s)

    return 0x0000, ds
    

# Implement the evt.EVT_N_SET handler
def handle_set(event):
    req = event.request
    if req.RequestedSOPInstanceUID not in managed_instances:
        # Failure - SOP Instance not recognised
        return 0x0112, None

    ds = managed_instances[req.RequestedSOPInstanceUID]

    # The N-SET request's *Modification List* dataset
    mod_list = event.attribute_list

    # Skip other tests...

    # TODO-DB: update your DB to record that this study acquisition is complete

    ds.update(mod_list)

    # Return status, dataset
    return 0x0000, ds


def find_worklist(requestedDS):

    worklist_objects = [] 
    sps_date = requestedDS.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate
    sps_modality = requestedDS.ScheduledProcedureStepSequence[0].Modality
    
    # TODO-DB: query your DB to get the planned exams for this modality and date
    appointments = [{
        "PatientID": "1234",
        "PatientName": "TEST^TEST",
        "PatientBirthDate": "19900101",
        "PatientSex": "U",
        "AppointmentDate": "20240101",
        "AppointmentTime": "100000",
        "AppointmentId": "4567"
    }]

    for a in appointments:

        ds = Dataset()
        ds.is_little_endian = True
        ds.is_implicit_VR = True
        # Add the necessary elements
        ds.PatientName = a["PatientName"]
        ds.PatientID = a["PatientID"]
        ds.SpecificCharacterSet = "ISO_IR 192"
        ds.PatientBirthDate = a["PatientBirthDate"]
        ds.PatientSex = a["PatientSex"]

        # Create the scheduled procedure step sequence
        sps = Dataset()
        sps.Modality = sps_modality
        sps.ScheduledStationAETitle = ""
        sps.ScheduledProcedureStepStartDate = a["AppointmentDate"]
        sps.ScheduledProcedureStepStartTime = a["AppointmentTime"]
        sps.ScheduledPerformingPhysicianName = ""
        sps.ScheduledProcedureStepDescription = ""        

        # Add the Scheduled Procedure Step Sequence to the dataset
        ds.ScheduledProcedureStepSequence = [sps]

        # Add other necessary elements (this is a minimal example, you may need to add more elements)
        ds.AccessionNumber = a["AppointmentId"]
        ds.StudyInstanceUID = generate_uid()

        ds.StudyID = a["AppointmentId"]
        worklist_objects.append(ds)
    return worklist_objects


# Define a handler for the C-ECHO request (Verification)
def handle_echo(event):
    """Handle a C-ECHO request event."""
    return 0x0000


def OnChange(changeType, level, resourceId):
    global worklist_server

    try:
        # start the worklist server when Orthanc starts
        if changeType == orthanc.ChangeType.ORTHANC_STARTED:

            # Define your custom AE title & port
            mpps_aet = json.loads(orthanc.GetConfiguration()).get('MPPSAet', "ORTHANC")
            mpps_port = json.loads(orthanc.GetConfiguration()).get('DicomPortMPPS', 4243)            

            # Specify the supported Transfer Syntaxes
            transfer_syntaxes = [
                ExplicitVRLittleEndian,
                ImplicitVRLittleEndian,
                ExplicitVRBigEndian,
            ]

            # Create the Application Entity with the custom AE title
            ae = pynetdicom.AE(ae_title=mpps_aet)
            ae.add_supported_context(ModalityPerformedProcedureStep)
            ae.add_supported_context(ModalityWorklistInformationFind)
            ae.add_supported_context(Verification)

            handlers = [(evt.EVT_N_CREATE, handle_create), (evt.EVT_N_SET, handle_set), (evt.EVT_C_FIND, handle_find), (evt.EVT_C_ECHO, handle_echo)]
            worklist_server = ae.start_server(('0.0.0.0', mpps_port), block = False, evt_handlers = handlers)
            
            orthanc.LogWarning('Worklist server using pynetdicom has started')

        elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:
            orthanc.LogWarning('Stopping pynetdicom Worklist server ')
            worklist_server.shutdown()   

    except Exception as e:
        s = str(e)
        orthanc.LogWarning("Error occured: %s" % s)


orthanc.RegisterOnChangeCallback(OnChange)
