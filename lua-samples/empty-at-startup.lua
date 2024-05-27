-- This script empties Orthanc at startup

-- method called by Orthanc at startup
function Initialize()
  -- get all instances
  print("-------------- Starting emptying script...")
  local allInstancesIds = ParseJson(RestApiGet("/instances"))

  -- delete each instance
  for i, instanceId in pairs(allInstancesIds) do
    RestApiDelete("/instances/" .. instanceId)
  end

  print("-------------- Orthanc is empty!")
end