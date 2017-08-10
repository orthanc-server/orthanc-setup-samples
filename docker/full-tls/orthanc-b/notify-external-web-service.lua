function OnStoredInstance(instanceId, tags, metadata, origin)
   -- everytime an instance is received, send a request to the external-web-service via the forward-proxy that will add a client certificate to the request
   print('received an instance.  Will notify the external-web-service')
   
   local response = HttpPost('http://orthanc-b-forward-proxy:8000/', 'received an instance ' .. instanceId)
   print('response received from the external-web-service: ' .. response)

end