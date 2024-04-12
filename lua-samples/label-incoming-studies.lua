function makeValidLabel(input)
    local invalidCharacters = "[^%w_-]"   -- everything that is not alphanumeric or _ or -
    return input:gsub(invalidCharacters, "-")
  end
  
  function OnStoredInstance(instanceId, tags, metadata)
    print("OnStoredInstance ...")
    PrintRecursive(metadata)
  
    local parentStudy = ParseJson(RestApiGet("/instances/" .. instanceId .. "/study"))
    if #parentStudy.Labels == 0 then
      print("OnStoredInstance adding labels to parent study")
      RestApiPut("/studies/" .. parentStudy.ID .. "/labels/called-" .. makeValidLabel(metadata.CalledAET), '')
      RestApiPut("/studies/" .. parentStudy.ID .. "/labels/ip-" .. makeValidLabel(metadata.RemoteIP), '')
      RestApiPut("/studies/" .. parentStudy.ID .. "/labels/remote-" .. makeValidLabel(metadata.RemoteAET), '')
    end
  
    print("OnStoredInstance ... done")
  
  end