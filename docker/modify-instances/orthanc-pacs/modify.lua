-- This sample shows how to use Orthanc to modify incoming instances.

function OnStoredInstance(instanceId, tags, metadata, origin)
   -- Do not process twice the same file
   if origin['RequestOrigin'] ~= 'Lua' then

      local modifyRequest = {}
      
      modifyRequest["Remove"] = {}
      table.insert(modifyRequest["Remove"], "OperatorsName")
      
      modifyRequest["Replace"] = {}
      modifyRequest["Replace"]["InstitutionName"] = "Orthanc Demo Hospital"
      modifyRequest["Replace"]["SOPInstanceUID"] = tags["SOPInstanceUID"]
      modifyRequest["Force"] = true  -- because we want to keep the same SOPInstanceUID

      -- download a modified version of the instance
      local modifiedDicom = RestApiPost('/instances/' .. instanceId .. '/modify', DumpJson(modifyRequest))

      -- upload the modified instance.  When performing modification at the instance level, all IDs from the original instance
      -- are preserved (SOPInstanceUID, SeriesInstanceUID, StudyInstanceUID)
      -- so when you'll upload it to Orthanc, it will overwrite the old instance only
      -- if you've set the "OverwriteInstances" option to true in your configuration file
      local uploadResponse = ParseJson(RestApiPost('/instances', modifiedDicom))

      -- PrintRecursive(uploadResponse)
      
      if (uploadResponse["Status"] == 'AlreadyStored') then
         print("Are you sure you've enabled 'OverwriteInstances' option ?")
      end

      if (uploadResponse["ID"] ~= instanceId) then
         print("modified instance and original instance don't have the same Orthanc IDs !")
      end 

      print('replaced InstitutionName in instance ' .. instanceId)

   end
end

function OnStableStudy(studyId, tags, metadata)
   -- since we have modified tags that are stored in the Index DB at Study/Series level: InstitutionName and OperatorsName,
   -- we need to reconstruct the Index DB data for this study

   RestApiPost('/studies/' .. studyId .. '/reconstruct', "")

   print('reconstructed Index DB data for study ' .. studyId)

end