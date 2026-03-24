function string:startswith(start)
    -- print(' ------ starts with -- ' .. start)
    return self:sub(1, #start) == start
end

function OutgoingCStoreInstanceFilter(dicom, destination)
    -- print(' -------- filtering outgoing instance ---- ' .. destination['RemoteAet'] .. " / " .. dicom.SOPInstanceUID .. " / " .. dicom.SOPClassUID)

    -- Don't send PDF or RGB images to 'CVIRES02'
   if destination['RemoteAet'] == 'CVIRES02' and (dicom.SOPClassUID:startswith('1.3.12.2.1107.5.9.1') or dicom.PhotometricInterpretation == 'RGB') then
        -- print(' -------- skipping instance ---- ' .. dicom.SOPInstanceUID)
        return false
   else
        return true
   end
end