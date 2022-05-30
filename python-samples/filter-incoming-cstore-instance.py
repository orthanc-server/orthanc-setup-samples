import orthanc

# this script accepts 2 instances from STORESCU and then, rejects the next ones

storeScuInstanceCounter = 0

def FilterIncomingCStoreInstance(instance):
    global storeScuInstanceCounter

    origin = instance.GetInstanceOrigin()
    if origin == orthanc.InstanceOrigin.DICOM_PROTOCOL:  # should always be true in the CStore callback !
        remoteAet = instance.GetInstanceRemoteAet()
        
        if remoteAet == "STORESCU":
            storeScuInstanceCounter += 1
        if storeScuInstanceCounter >= 3:
            return 0x0700
    
    return 0x0000

orthanc.RegisterIncomingCStoreInstanceFilter(FilterIncomingCStoreInstance)
