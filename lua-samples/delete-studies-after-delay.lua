-- note: You should set "LuaHeartBeatPeriod": 60 to run this function every 60 seconds.
--       Executing lua code is blocking a lot of other activities in Orthanc so we must
--       make this code run as fast as possible.  That's why we only analyze a single study
--       at a time (the oldest one) and delete a single study at a time.
-- note: we have also added code to enable the cleanup only between midnight and 6AM while
--       Orthanc is quiet
-- note: this script requires "ExtendedFind" -> Orthanc 1.12.5+ and SQLite or PostgreSQL DB.


-- Function to return the expiration date in the same format as Orthanc metadata
function GetExpirationDate(deltaInSecondsFromNow)
    -- get 'now' from Orthanc to make sure the time is stored in the same TZ as LastUpdate.
    -- that would not be true if calling os.time()
    -- return os.date("%Y%m%dT%H%M%S", os.time() - deltaInSecondsFromNow)

    local now_orthanc_string = RestApiGet('/tools/now')
    local now_orthanc = os.time({ year = tonumber(now_orthanc_string:sub(1, 4)), 
                                  month = tonumber(now_orthanc_string:sub(5, 6)),
                                  day = tonumber(now_orthanc_string:sub(7, 8)),
                                  hour = tonumber(now_orthanc_string:sub(10, 11)),
                                  min = tonumber(now_orthanc_string:sub(12, 13)),
                                  sec = tonumber(now_orthanc_string:sub(14, 15))})

    return os.date("%Y%m%dT%H%M%S", now_orthanc - deltaInSecondsFromNow)    
end

function OnHeartBeat()

    -- the following statment enables execution of the heartbeat only between midnight and 6AM
    if tonumber(os.date("%H", os.time())) >= 6 then
        return
    end


    local expiration_period_in_seconds = 50 * 24 * 3600  -- 50 days

    -- get the oldest study in Orthanc
    local find_payload = '{"Level": "Study", "Expand": true, "Query":{}, "OrderBy": [{"Type": "Metadata", "Key": "LastUpdate", "Direction": "ASC"}], "Limit": 1}'
    local oldest_studies = ParseJson(RestApiPost('/tools/find', find_payload))

    if #oldest_studies > 0 then
        local oldest_study = oldest_studies[1]
        -- PrintRecursive(oldest_study)

        local min_last_update = GetExpirationDate(expiration_period_in_seconds)
        -- print(min_last_update)
        
        if oldest_study.LastUpdate < min_last_update then
            print('deleting study ' .. oldest_study.ID .. ' whose LastUpdate is ' .. oldest_study.LastUpdate)
            RestApiDelete('/studies/' .. oldest_study.ID)
        end
    end
    
  end