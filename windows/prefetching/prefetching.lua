function OnStableStudy(studyId, tags, metadata)
  --PrintRecursive(tags)
  
  --first forward this study to the Workstation
  local moveBody = {}
  moveBody["Synchronous"] = false
  moveBody["Resources"] = {}
  table.insert(moveBody["Resources"], studyId)

  -- print(DumpJson(moveBody))
  -- PrintRecursive(moveBody)
  local moveJobId = ParseJson(RestApiPost('/modalities/workstation/store', DumpJson(moveBody)))["ID"]
  print('moving current study to workstation in job ' .. moveJobId)
  --Retrieve PatientID

  local StudyInstanceUID = tags["StudyInstanceUID"]
  local PatientID = ParseJson(RestApiGet('/studies/' .. studyId .. '/patient'))["MainDicomTags"]["PatientID"]

  -- build the C-Find query to the PACS to explore all studies from this patient
  local queryBody = {}
  queryBody["Level"] = "Study"
  queryBody["Query"] = {}
  queryBody["Query"]["PatientID"] = PatientID

  -- PrintRecursive(queryBody)
  local queryId = ParseJson(RestApiPost('/modalities/pacs/query', DumpJson(queryBody)))["ID"]

  local queryResponse = ParseJson(RestApiGet('/queries/' .. queryId .. '/answers'))
  for k, v in pairs(queryResponse) do
    local study = ParseJson(RestApiGet('/queries/' .. queryId .. '/answers/' .. v .. '/content?simplify'))
    
    -- if the study is not the current one, send it directly from the PACS to the PRIOR server  
    if study["StudyInstanceUID"] ~= StudyInstanceUID then
      local retrieveBody = {}
      retrieveBody["TargetAet"] = "WORKSTATION"
      retrieveBody["Synchronous"] = false

      local retrieveResponse = ParseJson(RestApiPost('/queries/' .. queryId .. '/answers/' .. v .. '/retrieve', DumpJson(retrieveBody)))
      PrintRecursive(retrieveResponse)
    end
  end
end

function OnJobSuccess(jobId)
  local job = ParseJson(RestApiGet('/jobs/' .. jobId))

  if job["Type"] == "DicomModalityStore" then
    -- delete the study once it has been forwarded
    RestApiDelete('/studies/' .. job["Content"]["ParentResources"][1])
  end
end