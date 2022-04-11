function sanitize(s)
    -- remove all characters that you don't want to have in a path
    s = string.gsub(s, " ", "-")
    s = string.gsub(s, "/", "-")
    s = string.gsub(s, "\\", "-")
 
    return s
 end
 
 function OnStoredInstance(instanceId, tags, metadata, origin)
    -- store files in a more human friendly hierarchy and then, delete the instance from Orthanc
 
    local institutionName = sanitize(tags["InstitutionName"])
    local patientId = sanitize(tags["PatientID"])
    local studyId = tags["StudyInstanceUID"]
    local seriesId = tags["SeriesInstanceUID"]
    local sopInstanceId = tags["SOPInstanceUID"]
 
    if (institutionName == nil or institutionName == "") then
         print("no InstitutionName, don't know what to do")
    else
       local dicom = RestApiGet('/instances/' .. instanceId .. '/file')
       local folder = "/tmp/dicom-files/" .. institutionName .. "/" .. patientId .. "/" .. studyId .. "/" .. seriesId 
       os.execute("mkdir -p " .. folder)
       local path = folder .. "/" .. sopInstanceId .. ".dcm" 
       local file = io.open(path, "w")
       io.output(file)
       io.write(dicom)
       io.close(file)
 
       Delete(instanceId) 
     end
 end