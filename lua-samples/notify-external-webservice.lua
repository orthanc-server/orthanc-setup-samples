-- this script notifies an external web-service each time a study gets stable
function OnStableStudy(studyId, tags, metadata, origin)
   
    -- get study and patient main dicom tags from Orthanc API
    local studyData = ParseJson(RestApiGet('/studies/' .. studyId))
    
    local accessionNumber = tags['AccessionNumber']
    local examination = tags['StudyDescription']
    local studyDate = tags['StudyDate']
    local modality = tags['Modality']
    
    local patientMainDicomTags = studyData['PatientMainDicomTags']
    local patientName = patientMainDicomTags['PatientName']
    local hospitalNumber = patientMainDicomTags['PatientID']
    local dob = patientMainDicomTags['PatientBirthDate']
    local sex = patientMainDicomTags['PatientSex']
 
    -- build the payload for the external web-service
    local payload = {
        ["Data"] = {
            ["AccessionNumber"] = accessionNumber,
            ["Examination"] = examination,
            ["StudyDate"] = studyDate,
            ["Modality"] = modality,
            ["PatientName"] = patientName,
            ["DOB"] = dob,
            ["Sex"] = sex,
            ["PatientId"] = hospitalNumber
        }
    }
 
    -- serialize the payload to json (the second "true" argument - keepStrings
    -- ensures that strings containing numbers, e.g. the StudyDate, are not transformed into numbers)
    local jsonStr = DumpJson(payload, true)
    
    print("payload: " .. jsonStr)
    
    local rawResponse = HttpPost("http://httpbin.org/post", 
        jsonStr, 
        {
            ["Content-Type"] = "application/json"
        }
    )

    -- local rawResponse = HttpPost("http://invalid.url.to.get.an.error", 
    --     jsonStr, 
    --     {
    --         ["Content-Type"] = "application/json"
    --     }
    -- )

    -- if the call fails, the response will be nil
    if (rawResponse) then
        -- transform the response into a lua table for internal processing
        local response = ParseJson(rawResponse)
        print("response: " .. rawResponse)
        PrintRecursive(response)
    else
        print("error while requesting external web-service (no error details, check the Orthanc logs in verbose mode)")
    end
 end
  