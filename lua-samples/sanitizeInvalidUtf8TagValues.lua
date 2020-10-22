-- This lua script has been used to sanitize Dicom tags that contained invalid UTF-8 characters

function fixUTF8(s, replacement)
  local p, len, invalid = 1, #s, {}
  while p <= len do
    if     p == s:find("[%z\1-\127]", p) then p = p + 1
    elseif p == s:find("[\194-\223][\128-\191]", p) then p = p + 2
    elseif p == s:find(       "\224[\160-\191][\128-\191]", p)
        or p == s:find("[\225-\236][\128-\191][\128-\191]", p)
        or p == s:find(       "\237[\128-\159][\128-\191]", p)
        or p == s:find("[\238-\239][\128-\191][\128-\191]", p) then p = p + 3
    elseif p == s:find(       "\240[\144-\191][\128-\191][\128-\191]", p)
        or p == s:find("[\241-\243][\128-\191][\128-\191][\128-\191]", p)
        or p == s:find(       "\244[\128-\143][\128-\191][\128-\191]", p) then p = p + 4
    else
      s = s:sub(1, p-1)..replacement..s:sub(p+1)
      table.insert(invalid, p)
    end
  end
  return s, invalid
end
 
function OnStoredInstance(instanceId, tags, metadata)
 
    -- Ignore the instances that result from a modification to avoid
    -- infinite loops
    if (metadata['ModifiedFrom'] == nil and
        metadata['AnonymizedFrom'] == nil) then
     
        if (tags["SpecificCharacterSet"] == "ISO_IR 192") then
            local mainDicomTags = {"PerformedProcedureStepDescription", "PatientID"}  -- TODO: complete with all main dicom tags that contain strings
            local tagsToModify = {}
            local needsModification = false
             
            for i,v in ipairs(mainDicomTags) do
                local tagValue = tags[v]
                local validTagValue = fixUTF8(tagValue, "?")
                if tagValue ~= validTagValue then
                    print('tag value for ' .. v .. ' does not contain valid utf8: ' .. tagValue)
                    tagsToModify[v] = validTagValue
                    needsModification = true
                end
            end
            
            if needsModification then
                print("we are going to modify the instance")
                PrintRecursive(tagsToModify)
                local removeTags = {}
                local modifiedInstanceId = ModifyInstance(instanceId, tagsToModify, removeTags, true)
                Delete(instanceId)  -- delete original instance
            end
 
        end
    end
end