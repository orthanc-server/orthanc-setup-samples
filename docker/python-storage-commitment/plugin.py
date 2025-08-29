import orthanc
import json
import pprint

# this plugins Stabilizes a study as soon as a storage commitment request has been received for all its instances

def storage_commitment_scp_callback(job_id, transaction_uid, requested_sop_class_uids, requested_sop_instance_uids, remote_aet, called_aet):
    # At the beginning of a Storage Commitment operation, you can build a custom data structure
    # that will be provided as the "data" argument in the StorageCommitmentLookup

    orthanc.LogInfo("Received storage commitment: building data structure")

    # we build a dico with all instances as keys.  We will remove them
    requested_instances = {}  # keep track of the sop_class_uids (as stored in Orthanc)
    parent_studies_ids = set()    
    studies = {} # keep track of all instances of each study (as stored in Orthanc)

    try:
        for i in range(0, len(requested_sop_instance_uids)):
            lookup = json.loads(orthanc.RestApiPost("/tools/lookup", requested_sop_instance_uids[i]))
        
            if len(lookup) != 1:
                requested_instances[requested_sop_instance_uids[i]] = None  # not found in Orthanc (or multiple instances with the same SOPInstanceUID: we are not able to differentiate them)
            else:
                instance_id = lookup[0]['ID']

                sop_class_uid_in_orthanc = json.loads(orthanc.RestApiGet(f"/instances/{instance_id}/metadata?expand"))['SopClassUid']
                parent_study_id = json.loads(orthanc.RestApiGet(f"/instances/{instance_id}/study"))['ID']

                requested_instances[requested_sop_instance_uids[i]] = sop_class_uid_in_orthanc

                parent_studies_ids.add(parent_study_id)

        pprint.pprint(parent_studies_ids)

        # check if all the requested instances are actually stored in Orthanc   
        for parent_study_id in parent_studies_ids:
            studies[parent_study_id] = []
            study_instances = json.loads(orthanc.RestApiGet(f"/studies/{parent_study_id}/instances"))
            
            for study_instance in study_instances:
                studies[parent_study_id].append(study_instance['MainDicomTags'].get('SOPInstanceUID'))

            pprint.pprint(studies[parent_study_id])

            for requested_sop_instance_uid in requested_sop_instance_uids:
                if requested_sop_instance_uid in studies[parent_study_id]:
                    studies[parent_study_id].remove(requested_sop_instance_uid)

            if len(studies[parent_study_id]) == 0:  # all the instances of the study have been requested in the Storage Commitment -> consider the study as stable
                orthanc.LogInfo(f"The study {parent_study_id} is complete, stabilizing it")
                # ret, hasStableStatusChanged = orthanc.SetStableStatus(parent_study_id, orthanc.StableStatus.STABLE)
                orthanc.SetStableStatus(parent_study_id, orthanc.StableStatus.STABLE)
    
        return requested_instances
    
    except Exception as e:
        orthanc.LogError("Error in StorageCommitment SCP: " + e)
        return None


# Reference: `StorageCommitmentScpJob::Lookup` in `OrthancServer/Sources/ServerJobs/StorageCommitmentScpJob.cpp`
def storage_commitment_lookup(requested_sop_class_uid, requested_sop_instance_uid, data):
    success = False
    reason = orthanc.StorageCommitmentFailureReason.NO_SUCH_OBJECT_INSTANCE

    orthanc.LogInfo(f"Storage commitment: handling {requested_sop_instance_uid}")    

    requested_instances = data
    pprint.pprint(requested_instances)

    # First check if the sop_class_uid requested in the storage commitment is the same as the one stored in Orthanc
    if requested_sop_instance_uid in requested_instances:
        if requested_instances[requested_sop_instance_uid] == requested_sop_class_uid:
            success = True
            reason = orthanc.StorageCommitmentFailureReason.SUCCESS
        else:
            reason = orthanc.StorageCommitmentFailureReason.CLASS_INSTANCE_CONFLICT

    orthanc.LogInfo("  Storage commitment SCP job: " + ("Success" if success else "Failure") + \
                    " while looking for " + requested_sop_class_uid + " / " + requested_sop_instance_uid)

    return reason

orthanc.RegisterStorageCommitmentScpCallback(storage_commitment_scp_callback, storage_commitment_lookup)