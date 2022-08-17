import orthanc
import json
import pprint
import os
import requests
import base64

mode = os.environ.get("FILTER_MODE", "modify-query;filter-results") # enable 2 modes by default !

def OnRestToolsFind(output, uri, **request):
    print('Accessing uri in python: %s' % uri)
    pprint.pprint(request)

    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')
    else:
        query = json.loads(request['body'])
        is_expand = query["Expand"] if "Expand" in query else False
        is_full = query["Full"] if "Full" in query else False
        level = query["Level"]

        if level != "Series":
            raise NotImplementedError()

        # in 'modify-query' mode, we modify the tools/find query to add the InstitutionName such that Orthanc performs a first filter
        if "modify-query" in mode:
            if "authorization" in request["headers"]:
                user = base64.b64decode(request["headers"]["authorization"].replace("Basic ", "")).decode('utf-8').split(':')[0]
                institution_name = requests.get(f"http://auth-service:8000/users/{user}").json()["institution"]
            elif "api-key" in request["headers"]:
                api_key = request["headers"]["api-key"]
                institution_name = requests.get(f"http://auth-service:8000/users/{api_key}").json()["institution"]
            query["Query"]["InstitutionName"] = institution_name

            print('Modified query:')
            pprint.pprint(query)

        # in "external" mode, we call an external web-service that will mimick tools/find and return results based on user access rights (and based on other fields from the query)
        if "external-app" in mode:
            answers = []
            pass   # TODO: call a web-service to perform the find based on user access rights
        else:
            answers = json.loads(orthanc.RestApiPost('/tools/find', json.dumps(query)))

        # in 'filter-results' mode, we cycle through all the answers from tools/find and remove the results that are not accessible to the user
        if "filter-results" in mode:
            filtered_answers = []
            for answer in answers:
                if is_expand:
                    # pprint.pprint(answer)
                    if is_full:
                        dicom_uid = answer["MainDicomTags"]["0020,000d"]["Value"]
                        orthanc_id = answer["ID"]
                    else:
                        dicom_uid = answer["MainDicomTags"]["StudyInstanceUID"]
                        orthanc_id = answer["ID"]
                else:
                    dicom_uid = None
                    orthanc_id = answer

                # perform the same call as the authorization plugin (= ask, for every resource, if the resource is accessible to this user)

                auth_query = {
                    "dicom-uid": dicom_uid,
                    "orthanc-id": orthanc_id,
                    "level": "study",
                    "method": "get"    # although we are in POST tools/find, we want to test "read" access to the study
                }
                
                # copy the auth headers from the request received by Orthanc (the auth-plugin needs them to identify the user)
                headers = {}
                if "authorization" in request["headers"]:
                    headers["authorization"] = request["headers"]["authorization"]
                    auth_query["token-key"] = "authorization"
                    auth_query["token-value"] = request["headers"]["authorization"]
                if "api-key" in request["headers"]:
                    headers["api-key"] = request["headers"]["api-key"]
                    auth_query["token-key"] = "api-key"
                    auth_query["token-value"] = request["headers"]["api-key"]

                auth_response = requests.post("http://auth-service:8000/auth/validate", json=auth_query, headers=headers).json()
                if auth_response["granted"]:
                    filtered_answers.append(answer)

            answers = filtered_answers

        output.AnswerBuffer(json.dumps(answers), 'application/json')

orthanc.RegisterRestCallback('/tools/find', OnRestToolsFind)
