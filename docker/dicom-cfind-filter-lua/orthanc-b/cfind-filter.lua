function IsIdSpecificEnough(id, minimumLengthIfContainsWildcard)

    if (id == nil) then -- if the id is not defined, it's not specific at all
        return false
    end

    if (string.find(id, '*') == nil and string.len(id) ~= 0) then  -- if there's no wildcard or if string is empty, the user expects an exact match -> this is specific !
        return true
    end

    if (minimumLengthIfContainsWildcard ~= nil and string.len(id) >= minimumLengthIfContainsWildcard) then -- if there's a wildcard, make sure there are enough characters in the criteria to make it specific
        return true
    end

    return false
end

function IncomingFindRequestFilter(query, origin)

    -- PrintRecursive(query)
    
    -- right now, we consider that when they request SERIES or INSTANCES, they will provide specific IDs so we won't filter them
    if (query['0008,0052'] ~= "STUDY" and query['0008,0052'] ~= "PATIENT") then
        return query
    end

    -- make sure the request is specific enough and will not return too many results
    local specificIdentifierFound = false
    local dateRangeIsSmallEnough = false

    -- check PatientID
    -- local patientID = query['0010,0020']
    if (IsIdSpecificEnough(query['0010,0020'], 7)) then -- patientID ~= nil and string.len(patientID) >= 7) then
        specificIdentifierFound = true
    end
    -- check PatientName
    if (IsIdSpecificEnough(query['0010,0010'], 4)) then
        specificIdentifierFound = true
    end
    -- check StudyInstanceUID
    if (IsIdSpecificEnough(query['0020,000d'], nil)) then
        specificIdentifierFound = true
    end
    -- check AccessionNumber
    if (IsIdSpecificEnough(query['0008,0050'], 4)) then
        specificIdentifierFound = true
    end

    -- if no identifier, make sure the date range is small enough
    if (not specificIdentifierFound) then

        local studyDate = query['0008,0020']
        if (studyDate ~= nil) then
            if (string.len(studyDate) == 8) then -- studyDate is a single day
                dateRangeIsSmallEnough = true
            elseif (string.len(studyDate) > 8) then

                local fromDicomDate = os.date("%Y%m%d", os.time{year=1900, month=1, day=1})
                local toDicomDate = os.date("%Y%m%d", os.time())

                if (string.len(studyDate) == 9 and string.sub(studyDate, 9, 9) == '-') then -- studyDate is a date range with only a fromDate
                    fromDicomDate = string.sub(studyDate, 1, 8)
                
                elseif (string.len(studyDate) == 17) then -- studyDate is a date range
                    fromDicomDate = string.sub(studyDate, 1, 8)
                    toDicomDate = string.sub(studyDate, 9, 17)
                end
                
                local from = os.time{year=string.sub(fromDicomDate, 1, 4), month=string.sub(fromDicomDate, 5, 6), day=string.sub(fromDicomDate, 7, 8)}
                local to = os.time{year=string.sub(toDicomDate, 1, 4), month=string.sub(toDicomDate, 5, 6), day=string.sub(toDicomDate, 7, 8)}

                local dateRangeInDays = (to - from)/(3600 * 24)

                if (dateRangeInDays > 7.5) then -- during DST, we might have 6.9 or 7.1 so, let's take some margin :-)
                    print("CFind-filter: dateRange is too large: " .. dateRangeInDays .. " days")
                else
                    dateRangeIsSmallEnough = true
                end

            end
        end
    end

    -- if the query is not specific enough, make sure the query does not return any results at all
    if (not specificIdentifierFound and not dateRangeIsSmallEnough) then
        print("the C-Find query is not specific enough, no results will be returned")
        PrintRecursive(query)
        
        -- let's specifying a StudyInstanceUID that will not match
        query['0020,000d'] = "0.0.0.0"
    end

    return query
end