function CheckForConfigurationUpdate()

    -- get current Orthanc configuration
    local current_config = GetOrthancConfiguration()

    PrintRecursive(current_config)

    local system_id = math.floor(current_config["SystemId"])

    local config_version = 0

    if current_config["ConfigVersion"] ~= nil then
        config_version = math.floor(current_config["ConfigVersion"])
    end
    

    -- download configuration from a remote web service
    SetHttpTimeout(1)  -- if the webservice is unresponsive, it is important that Orthanc is not locked too long waiting for the answer 
    local new_config = ParseJson(HttpGet("http://config-webservice:8000/configs/" .. system_id .. "?current_config_version=" .. config_version))

    -- config is nil if the webservice did not answer and empty if we already have the right config
    if new_config ~= nil and next(new_config) ~= nil then

        print("++++++++++++ replacing config +++++++++++++++++++++")
        PrintRecursive(new_config)
        local file = io.open("/etc/orthanc/orthanc-dynamic.json", "w")
        file:write(DumpJson(new_config))
        file:close()

        print("++++++++++++ restarting Orthanc with new config +++++++++++++++++++++")
        RestApiPost("/tools/reset", "")
    else
        print("No new configuration available, keeping this one")
    end

end

function OnHeartBeat()

    print("Lua Heart beat")
    CheckForConfigurationUpdate()

end

function Initialize()

    CheckForConfigurationUpdate()

end