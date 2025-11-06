-- This script sanitizes incoming instances whose StudyInstanceUID is actually
-- identical to the AccessionNumber

function OnStoredInstance(instanceId, tags, metadata, origin)

  -- Extract and Normalize Tags
  local accessionNumber = tostring(tags['AccessionNumber'])
  local studyInstanceUid = tostring(tags['StudyInstanceUID'])

  -- Exit if critical tags are missing
  if not accessionNumber or accessionNumber == '' or not studyInstanceUid or studyInstanceUid == '' then
    return
  end

  -- Perform the Logical Test
  if accessionNumber == studyInstanceUid then
    print("Updating Study Instance UID for accession number: " .. accessionNumber)

    -- check if this is the first time we encounter this AccessionNumber -> if yes, let's generate a new StudyInstanceUID
    local findPayload = {}
    findPayload["Level"] = "Study"
    findPayload["Query"] = {}
    findPayload["Query"]["AccessionNumber"] = tostring(accessionNumber)
    findPayload["ResponseContent"] = {}
    findPayload["ResponseContent"][1] = "MainDicomTags"

    -- PrintRecursive(findPayload)
    local newStudyInstanceUid = nil

    local findResults = ParseJson(RestApiPost('/tools/find', DumpJson(findPayload, true)))
    for i, v in ipairs(findResults) do
      if (v["MainDicomTags"]["StudyInstanceUID"] ~= accessionNumber) then  -- avoid this instance's parent study that still has the StudyInstanceUID == AccessionNumber
        newStudyInstanceUid = v["MainDicomTags"]["StudyInstanceUID"]
      	print("Reusing an existing StudyInstanceUID: " .. newStudyInstanceUid )
      end
    end

    if newStudyInstanceUid == nil then
      newStudyInstanceUid = RestApiGet('/tools/generate-uid?level=study')
    	print("Generated a new StudyInstanceUID: " .. newStudyInstanceUid)
    end

    -- modify the instance
    local modifyPayload = {}
    modifyPayload["Force"] = true
    modifyPayload["Replace"] = {}
    modifyPayload["Replace"]['StudyInstanceUID'] = newStudyInstanceUid
    modifyPayload["Replace"]['SeriesInstanceUID'] = tags['SeriesInstanceUID'] -- keep all other DICOM IDs unchanged to make the modification idempotent
    modifyPayload["Replace"]['SOPInstanceUID'] = tags['SOPInstanceUID']

    local modifiedInstanceContent = RestApiPost('/instances/' .. instanceId .. '/modify', DumpJson(modifyPayload, true))

    local newInstanceId = ParseJson(RestApiPost('/instances', modifiedInstanceContent))['ID']

    -- delete the source instance
    if (newInstanceId ~= instanceId) then  -- this should always be true since we have changed the StudyInstanceUID, the instance orthanc id will change.
      Delete(instanceId)
    end
      
    -- Log the action taken for troubleshooting
    print('Modified one instance of ' .. studyInstanceUid .. ' (Accession ' .. accessionNumber .. ') modified. New SUID: ' .. newStudyInstanceUid)

  end

end