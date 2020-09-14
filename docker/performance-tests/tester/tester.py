from orthancRestApi import OrthancClient, OrthancThreadedClient
import argparse
import time
import os
import queue
import requests
import threading
import zipfile
import shutil
from pathlib import Path

parser = argparse.ArgumentParser("Orhtanc disk performance tests")
parser.add_argument('-o', '--orthancUrl', help="the url of the orthanc to test", default = "http://localhost:8044")
parser.add_argument('-t', '--threadCount', help="the number of concurrentThreads", default = 10, type=int)
parser.add_argument("-u", "--upload", action="store_true", default=False)
parser.add_argument("-dt", "--downloadThreaded", action="store_true", default=False)
parser.add_argument("-dtn", "--downloadThreadedToDevNull", action="store_true", default=False)
parser.add_argument("-dm", "--downloadMonoThread", action="store_true", default=False)

args = parser.parse_args()

orthanc = OrthancClient(args.orthancUrl)
orthanc.waitStarted(20)

scriptFolder = os.path.abspath(os.path.dirname(__file__))
sourceImageRootPath = os.path.join(scriptFolder, "images")
zipRootPath = os.path.join(sourceImageRootPath, "zip")

Path(zipRootPath).mkdir(parents=True, exist_ok=True)
Path(sourceImageRootPath).mkdir(parents=True, exist_ok=True)

cardioId = "595df1a1-74fe920a-4b9e3509-826f17a3-762a2dc3"
mammoId = "159f0c3d-99072051-6146da1c-02c9fe9a-5632fd15"
oncoId = "4e8a6235-aab12c38-adc2731f-0cd52bbe-2352e81f"

def downloadSourceImages(studyId, name):
  print(f"downloading source images - {name} - {studyId} ...")
  zipPath = os.path.join(zipRootPath, f"{name}.zip")
  imagesPath = os.path.join(sourceImageRootPath, name)
  Path(imagesPath).mkdir(parents=True, exist_ok=True)
  
  # r = requests.get(f"http://viewer-basic.osimis.io/series/40d9ffeb-d870d6ae-d1ce5c4f-26db135d-abf6abf4/archive")
  r = requests.get(f"http://viewer-basic.osimis.io/studies/{studyId}/archive", timeout = 300)
  open(zipPath, "wb").write(r.content)

  with open(zipPath, "rb") as f:
    zf = zipfile.ZipFile(f)
    zf.extractall(imagesPath)

if not os.path.exists(os.path.join(sourceImageRootPath, "cardio")):
  downloadSourceImages(cardioId, "cardio")
if not os.path.exists(os.path.join(sourceImageRootPath, "mammo")):
  downloadSourceImages(mammoId, "mammo")
if not os.path.exists(os.path.join(sourceImageRootPath, "onco")):
  downloadSourceImages(oncoId, "onco")

print(f"Using {args.threadCount} concurrent HTTP client")
ot = OrthancThreadedClient(orthancClient = orthanc, threadCount = args.threadCount)


def uploadFolder(title, threaded, folder, studyId):
  print(f"upload - {title} ...")
  orthanc.studies.delete(studyId, ignoreNotFoundErrors=True)

  startTime = time.time()
  if threaded:
    ot.uploadFolder(folder)
  else:
    orthanc.uploadFolder(folder)

  elapsed = round(time.time() - startTime, 3)
  print(f"{title}: {elapsed} s")
  return elapsed

def downloadFolder(title, threaded, studyId):
  print(f"download - {title} ...")

  downloadPath = os.path.join(sourceImageRootPath, "downloads")
  shutil.rmtree(downloadPath, ignore_errors=True)
  Path(downloadPath).mkdir(parents=True, exist_ok=True)

  instancesIds = orthanc.studies.getInstancesIds(studyId)

  startTime = time.time()
  if threaded:
    ot.downloadInstances(instancesIds, downloadPath)
  else:
    orthanc.instances.downloadInstances(instancesIds, downloadPath)

  elapsed = round(time.time() - startTime, 3)
  print(f"{title}: {elapsed} s")
  return elapsed

def downloadInstancesToDevNullThread(i: int, source: queue.Queue):
  while True:
    instanceId = source.get()
    if instanceId is None:
      return

    orthanc.instances.getDicom(instanceId)

def downloadToDevNull(title, studyId):
  print(f"download to /dev/null - {title} ...")
  source = queue.Queue()
  threads = []

  instancesIds = orthanc.studies.getInstancesIds(studyId)

  startTime = time.time()

  for i in range(0, args.threadCount):
    threads.append(threading.Thread(target = downloadInstancesToDevNullThread, args = (i, source, )))
    threads[i].start()

  for instanceId in instancesIds:
    source.put(instanceId)

  for i in range(0, args.threadCount):
    source.put(None)  # stop

  for i in range(0, args.threadCount):
    threads[i].join()

  elapsed = round(time.time() - startTime, 3)
  print(f"{title}: {elapsed} s")
  return elapsed







if args.upload:
  uploadFolder("warming up source disk cache", False, os.path.join(sourceImageRootPath, "cardio"), cardioId)
  uploadFolder("upload cardio 1 thread  :", False, os.path.join(sourceImageRootPath, "cardio"), cardioId)
  uploadFolder("upload cardio threaded :", True, os.path.join(sourceImageRootPath, "cardio"), cardioId)

  uploadFolder("warming up source disk cache", False, os.path.join(sourceImageRootPath, "onco"), oncoId)
  uploadFolder("upload onco 1 thread  :", False, os.path.join(sourceImageRootPath, "onco"), oncoId)
  uploadFolder("upload onco threaded :", True, os.path.join(sourceImageRootPath, "onco"), oncoId)

  uploadFolder("warming up source disk cache", False, os.path.join(sourceImageRootPath, "mammo"), mammoId)
  uploadFolder("upload mammo 1 thread  :", False, os.path.join(sourceImageRootPath, "mammo"), mammoId)
  uploadFolder("upload mammo threaded :", True, os.path.join(sourceImageRootPath, "mammo"), mammoId)

if args.downloadThreaded:
  downloadFolder("download mammo threaded", True, mammoId)
  downloadFolder("download cardio threaded", True, cardioId)
  downloadFolder("download onco threaded", True, oncoId)
    

if args.downloadMonoThread:
  downloadFolder("download mammo 1 thread", False, mammoId)
  downloadFolder("download cardio 1 thread", False, cardioId)
  downloadFolder("download onco 1 thread", False, oncoId)
  
if args.downloadThreadedToDevNull:
  # downloadToDevNull("download mammo to dev null - threaded", mammoId)
  # downloadToDevNull("download cardio to dev null - threaded", cardioId)
  downloadToDevNull("download onco to dev null - threaded", oncoId)