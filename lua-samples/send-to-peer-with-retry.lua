
function OnStoredInstance(instanceId, tags, metadata)
  local moveRequest = {}
  moveRequest["Resources"] = {}
  table.insert(moveRequest["Resources"], instanceId)
  moveRequest["Asynchronous"] = true

  local job = ParseJson(RestApiPost("/peers/peer-a/store", DumpJson(moveRequest, true)))
  print("created job " .. job["ID"] .. " to transfer instance " .. instanceId)
end

function OnJobFailure(jobId)
  print("job " .. jobId .. " failed")

  local job = ParseJson(RestApiGet("/jobs/" .. jobId))
  -- PrintRecursive(job)

  if job["Type"] == "OrthancPeerStore" then
    -- display debug info on the failing instance
    local instanceId = job["Content"]["ParentResources"][1]
    local instance = ParseJson(RestApiGet("/instances/" .. instanceId ..))
    PrintRecursive(instance)

    -- if you want to perform a retry, uncomment the line below ...
    -- RestApiPost("/jobs/" .. jobId .. "/resubmit", "")
  end

end