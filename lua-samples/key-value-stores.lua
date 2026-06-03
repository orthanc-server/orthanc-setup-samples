function OnStoredInstance(instanceId, tags, metadata)
    print('--- in OnStoredInstance ---')

    StoreKeyValue('my-store-id', instanceId, tags.SOPInstanceUID)
end

function OnStableSeries(seriesId, tags, metadata)
    print('--- in StableSeries ----')

    local instancesIds = ParseJson(RestApiGet('/series/' .. seriesId .. '/instances?expand=false'))

    for i, instanceId in pairs(instancesIds) do
        print('-- getting value for key "' .. instanceId .. '"')
        local value = GetKeyValue('my-store-id', instanceId)
        print('-- value for key "' .. instanceId .. '" is "' .. value .. '"')

        DeleteKeyValue('my-store-id', instanceId)
        value = GetKeyValue('my-store-id', instanceId)
        if value ~= nil then
            print('-- the value is still there --')
        else
            print('-- the value has been deleted --')
        end
    end

end