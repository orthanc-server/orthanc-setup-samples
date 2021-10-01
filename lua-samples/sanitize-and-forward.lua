function OnStoredInstance(instanceId, tags, metadata, origin)
    -- Do not process twice the same file
    if origin['RequestOrigin'] ~= 'Lua' then
 
       local modifyRequest = {}
       
       modifyRequest["Remove"] = {}
       table.insert(modifyRequest["Remove"], "0028-3010")
       
       modifyRequest["Replace"] = {}
       modifyRequest["Replace"]["SOPInstanceUID"] = tags["SOPInstanceUID"]
       modifyRequest["Force"] = true  -- because we want to keep the same SOPInstanceUID
 
       -- download a modified version of the instance
       local modifiedDicom = RestApiPost('/instances/' .. instanceId .. '/modify', DumpJson(modifyRequest))
 
       RestApiPost('/modalities/target-modality/store-straight', modifiedDicom)

       RestApiDelete('/instances/' .. instanceId)
    end
 end