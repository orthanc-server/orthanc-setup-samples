function IncomingHttpRequestFilter(method, uri, ip, username, httpHeaders)

  if username == 'admin' then -- admin user can do anything
     return true
  elseif method == 'DELETE' and string.match(uri, '/patients/') then -- delete patient allowed only for certain users
     local patientInfo = ParseJson(RestApiGet(uri))
     PrintRecursive(patientInfo)

     print('user ' .. username ..' is trying to delete PatientID: ' .. patientInfo["MainDicomTags"]["PatientID"])

     -- todo: return true/false according to your criteria ...

     return false
  elseif method == 'DELETE' then  -- forbid all other deletes
     return false
  else -- everything else is allowed
     return true
  end
end



-- disable the anonymize route only
function IncomingHttpRequestFilter(method, uri, ip, username, httpHeaders)

   if method == 'POST' and string.match(uri, '/anonymize') then
      return false
   else -- everything else is allowed
      return true
   end
 end