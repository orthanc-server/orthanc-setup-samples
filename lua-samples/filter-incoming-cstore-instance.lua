function ReceivedCStoreInstanceFilter(dicom, origin, info)
     PrintRecursive(info)
     print(' -------- filtering incoming instance ---- ' .. origin['RemoteAet'] .. " / " .. dicom.SOPInstanceUID .. " / " .. dicom.SOPClassUID)

    -- Don't accept 'RGB' files from send uncommon Siemens specific SOPClasses or RGB images to 'CVIRES02'
   if (origin['RemoteAet'] == 'ORTHANC-SERV' and dicom.PhotometricInterpretation == 'RGB') then
        print(' -------- skipping instance ---- ' .. dicom.SOPInstanceUID)
        return 0xA700  -- out of resources: (any non zero DIMSE Status means that the instance will be discarded)
   else
        return 0x0000  -- success: accept the instance
   end
end