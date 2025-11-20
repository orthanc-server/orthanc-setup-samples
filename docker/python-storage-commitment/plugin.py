import orthanc
import json
import pprint
import logging

# this plugins Stabilizes a study as soon as a storage commitment request has been received for all its instances

def storage_commitment_scp_callback(job_id, transaction_uid, requested_sop_class_uids, requested_sop_instance_uids, remote_aet, called_aet):
    # At the beginning of a Storage Commitment operation, you can build a custom data structure
    # that will be provided as the "data" argument in the StorageCommitmentLookup

    orthanc.LogInfo("Received storage commitment: building data structure")

    # we build a dico with all instances as keys. We will remove them
    requested_instances = {}  # keep track of the sop_class_uids (as stored in Orthanc)
    parent_studies_ids = set()    
    requested_per_study = {}  # keep track of all requested instances per study (including missing)
    requested_sop_class_uids_by_sop_instance_uids = {} # Maps SOPInstanceUID to SOPClassUID

    try:
        mark_studies_stable = True

        # Build requested_per_study dictionary from all SC request UIDs
        for i in range(len(requested_sop_instance_uids)):
            sop_instance_uid = requested_sop_instance_uids[i]
            requested_sop_class = requested_sop_class_uids[i]
            requested_sop_class_uids_by_sop_instance_uids[sop_instance_uid] = requested_sop_class

            lookup = json.loads(orthanc.RestApiPost("/tools/lookup", sop_instance_uid))

            if len(lookup) != 1 or 'ID' not in lookup[0]:
                requested_instances[sop_instance_uid] = None
                mark_studies_stable = False
            else:
                instance_id = lookup[0]['ID']
                sop_class_uid_in_orthanc = json.loads(orthanc.RestApiGet(f"/instances/{instance_id}/metadata?expand"))['SopClassUid']
                parent_study_id = json.loads(orthanc.RestApiGet(f"/instances/{instance_id}/study"))['ID']

                requested_instances[sop_instance_uid] = sop_class_uid_in_orthanc

                parent_studies_ids.add(parent_study_id)

                if parent_study_id not in requested_per_study:
                    requested_per_study[parent_study_id] = set()
                requested_per_study[parent_study_id].add(sop_instance_uid)


        pprint.pprint(parent_studies_ids)

        for parent_study_id in parent_studies_ids:
            study_requested_uids = requested_per_study.get(parent_study_id, set())
            pprint.pprint(study_requested_uids)

            # Verify all requested instances for this study are present and match SOP Class
            all_success = True
            failed_uids = []
            for uid in study_requested_uids:
                requested_class = requested_sop_class_uids_by_sop_instance_uids.get(uid)
                stored_class = requested_instances.get(uid)

                if requested_class is None or stored_class is None:
                    all_success = False
                    failed_uids.append(uid)
                    continue
                if stored_class != requested_class:
                    all_success = False
                    failed_uids.append(uid)

            if all_success and mark_studies_stable:
                orthanc.LogInfo(f"The study {parent_study_id} is complete, stabilizing it")
                # ret, hasStableStatusChanged = orthanc.SetStableStatus(parent_study_id, orthanc.StableStatus.STABLE)
                orthanc.RestApiPut(
                    f"/studies/{parent_study_id}/metadata/1027", # StableStudyTrigger
                    "StorageCommitment"
                )
                orthanc.SetStableStatus(parent_study_id, orthanc.StableStatus.STABLE)
            else:
                orthanc.LogInfo(
                    f"The study {parent_study_id} is not fully committed, not stabilizing."
                    f"Missing or failed SOP Instance UIDs: {failed_uids}"
                )

        return requested_instances
    
    except Exception as e:
        orthanc.LogError("Error in StorageCommitment SCP: " + str(e))
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

    orthanc.LogInfo(" Storage commitment SCP job: " + ("Success" if success else "Failure") + \
                    " while looking for " + requested_sop_class_uid + " / " + requested_sop_instance_uid)

    return reason

orthanc.RegisterStorageCommitmentScpCallback(storage_commitment_scp_callback, storage_commitment_lookup)