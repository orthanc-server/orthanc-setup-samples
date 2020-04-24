from multiprocessing import Pool, Queue, Process
from functools import partial
import os
import json
import threading
import requests
import tempfile



class Sanitizer:

  def __init__(self, workerCount):
    self.workerCount = workerCount
    self.workers = []
    self.workersShouldStop = False
    self.instancesToProcess = Queue()


  def start(self):
    print("Starting {w} python workers for Sanitizer".format(w=self.workerCount))
    
    for i in range(0, self.workerCount):
      self.workers.append(Process(target=worker, group=None, args=(str(i), self, )))
      self.workers[i].start()


  def stop(self):
    print("Stoping {w} python workers for Sanitizer".format(w=self.workerCount))
    workersShouldStop = True
    
    # push one dummy message for each worker to wake them up
    for i in range(0, self.workerCount):
      instancesToProcess.put(None)

    for i in range(0, self.workerCount):
      self.workers[i].join()


  def push(self, instanceId: str):
    print("pushing instance " + instanceId)
    self.instancesToProcess.put(instanceId)


  def retryInstanceLater(self, instanceId: str, delay: float):
    t = threading.Timer(delay, function=self.push, args=(instanceId, ))
    t.start()


  def modifyInstance(self, instanceId: str):
    print("processing instance " + instanceId)

    # we are not in the Orthanc main process so we can't use the orthanc python module,
    # we have to use requests to access Orthanc from the external API
    orthancApi = requests.Session()
    orthancApi.auth = requests.auth.HTTPBasicAuth("python-script", "my-python-password")
    
    instanceTagsRequest = orthancApi.get(url="http://localhost:8042/instances/" + instanceId + "/tags?simplify")
    if instanceTagsRequest.status_code != 200:
        print("Could not get instance tags: " + instanceId + ", it won't be retried !")
        return

    try:
      # download a modified version of the instance
      modifyBody = {
        "Replace" : {
          "InstitutionName": "MY NEW INSTITUTION",
          "SOPInstanceUID": instanceTagsRequest.json()["SOPInstanceUID"]  # in Orthanc 1.6.1, we actually can't keep this value ! -> will be fixed in 1.7.0
        },
        "Keep": [
        ],
        "Force": True  # because we want to replace/keep the SOPInstanceUID
      }

      #print(json.dumps(modifyBody))
      modifyRequest = orthancApi.post(url="http://localhost:8042/instances/" + instanceId + "/modify", 
                                      data=json.dumps(modifyBody))

      if modifyRequest.status_code != 200:
        print("Could not modify instance: " + instanceId + ", it won't be retried !")
        return

      modifiedDicom = modifyRequest.content

      with tempfile.NamedTemporaryFile(delete=False) as uncompressed:
        uncompressed.file.write(modifiedDicom)
        
        with tempfile.NamedTemporaryFile(delete=False) as compressed:
          os.system("gdcmconv -U --j2k " + uncompressed.name + " " + compressed.name)

          with open(compressed.name, "rb") as f:
            sendToPacsRequest = orthancApi.post(url="http://localhost:8042/modalities/pacs/store-straight",
                                                data=f.read())

          if sendToPacsRequest.status_code == 200:
            print("instance sent to PACS, deleting")
            deleteRequest = orthancApi.delete(url="http://localhost:8042/instances/" + instanceId)

            if deleteRequest.status_code == 200:
              return
          else:
            print("instance failed to send to PACS, will retry later")
      
      self.retryInstanceLater(instanceId, 10.0)

    except Exception as e:
      print("could not process instance: {i}: {e}, will retry later".format(i=instanceId, e=e))
      self.retryInstanceLater(instanceId, 10.0)




def worker(workerName: str, sanitizer: Sanitizer):
  print("Starting python worker " + workerName)

  while not sanitizer.workersShouldStop:
    instanceId = sanitizer.instancesToProcess.get()

    if sanitizer.workersShouldStop:
      break

    sanitizer.modifyInstance(instanceId)

  print("Exiting python worker " + workerName)


# def retrier(sanitizer: Sanitizer):
#   orthanc.LogWarning("Starting python retrier")

#   while not sanitizer.workersShouldStop:
#     instanceId = sanitizer.instancesToProcess.get()

#     if sanitizer.workersShouldStop:
#       break

#     sanitizer.modifyInstance(instanceId)

#   orthanc.LogWarning("Exiting python retrier")
