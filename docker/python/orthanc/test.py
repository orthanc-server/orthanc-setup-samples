import orthanc
import pprint

def OnRest(output, uri, **request):
    pprint.pprint(request)
    print('Accessing uri: %s' % uri)
    output.AnswerBuffer('ok\n', 'text/plain')

orthanc.RegisterRestCallback('/(to)(t)o', OnRest)
orthanc.RegisterRestCallback('/tata', OnRest)