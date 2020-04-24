import os
import requests
import time
import pprint

os.system("docker-compose up --build -d")

print("uploading file to modality")
modality = requests.Session()
modality.auth = ("demo", "demo")
with open(os.path.dirname(os.path.realpath(__file__)) + "/../../dicomFiles/source.dcm", "rb") as f:
  instanceId = modality.post("http://localhost:8044/instances", f.read()).json()["ID"]

print("sending from modality to middleman")
modality.post("http://localhost:8044/modalities/middleman/store", instanceId)

print("wait for the instance to arrive on the PACS")
pacs = requests.Session()
pacs.auth = ("demo", "demo")

retries = 0
foundInstance = False

while retries < 10 and not foundInstance:
  try:
    instanceTagsOnPacsRequest = pacs.get("http://localhost:8042/instances/" + instanceId + "/tags?simplify", timeout = 1)
    metadataOnPacsRequest = pacs.get("http://localhost:8042/instances/" + instanceId + "/metadata?expand", timeout = 1)

    if instanceTagsOnPacsRequest.status_code == 200 and metadataOnPacsRequest.status_code == 200:
      foundInstance = True
    else:
      print("...")
      time.sleep(1)
      retries = retries + 1
  except:
    print("...")
    time.sleep(1)
    retries = retries + 1


if instanceTagsOnPacsRequest.json()["InstitutionName"] == "MY NEW INSTITUTION":
  print("InstitutionName has been updated")
else:
  print("InstitutionName has not been updated")

if metadataOnPacsRequest.json()["TransferSyntax"] == "1.2.840.10008.1.2.4.90":
  print("Image has been compressed to JP2K")
else:
  print("Image has not been compressed to JP2K")

os.system("docker-compose down")

