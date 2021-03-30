import orthanc


def OnRestInstances(output, uri, **request): 
  # pprint.pprint(request)
    
  if request['method'] == 'GET':
    answer_from_core_api = orthanc.RestApiGet('/instances')
    output.AnswerBuffer(answer_from_core_api, 'application/json') 
  
  elif request['method'] == 'POST':
    answer_from_core_api = orthanc.RestApiPost('/instances', request['body'])

    # do whatever you need here

    output.AnswerBuffer(answer_from_core_api, 'application/json') 


orthanc.RegisterRestCallback('/instances', OnRestInstances)

