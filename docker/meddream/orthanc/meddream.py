# this file is downloaded from https://www.softneta.com/files/meddreampacs/lite/meddream.py

import json
import orthanc
def GetStudyInfo(output, uri, **request):
    studyId = request['groups'][0]
    info = []
    instances = orthanc.RestApiGet('/studies/%s/instances?expand' % studyId)
    series = orthanc.RestApiGet('/studies/%s/series' % studyId)
    for serie in json.loads(series):
        tags = serie['MainDicomTags']
        tags['OrthancSeriesID'] = serie['ID']
        tags['ParentStudy'] = serie['ParentStudy']
        info1 = []

        for instance in json.loads(instances):
            if serie['ID'] == instance['ParentSeries']:
                tags1 = instance['MainDicomTags']
                tags1['OrthancInstanceID'] = instance['ID']
                metadata = orthanc.RestApiGet('/instances/%s/metadata?expand' % instance['ID'])
                for (key, value) in json.loads(metadata).items():
                    tags1[key] = value

                info1.append(tags1)
        tags['Instances'] = info1
        info.append(tags)


    output.AnswerBuffer(json.dumps(info), 'application/json')
orthanc.RegisterRestCallback('/studies/(.*)/info', GetStudyInfo)