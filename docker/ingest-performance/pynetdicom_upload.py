from pydicom import dcmread

from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import CTImageStorage
import os
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--dicom_port', type=int, default=5043)
parser.add_argument('--folder', type=str)
args = parser.parse_args()

# debug_logger()

# Initialise the Application Entity
ae = AE()

# Add a requested presentation context
ae.add_requested_context(CTImageStorage)

# Read in our DICOM CT dataset
root_folder = args.folder


# Associate with peer AE at IP 127.0.0.1 and port 11112
assoc = ae.associate('127.0.0.1', args.dicom_port)
if assoc.is_established:
    for path in glob.glob(os.path.join(root_folder, '**/*.dcm')):

        ds = dcmread(path)
        # Use the C-STORE service to send the dataset
        # returns the response status as a pydicom Dataset
        status = assoc.send_c_store(ds)

        # Check the status of the storage request
        if status:
            # If the storage request succeeded this will be 0x0000
            #print('C-STORE request status: 0x{0:04x}'.format(status.Status))
            pass
        else:
            print('Connection timed out, was aborted or received invalid response')

    # Release the association
    assoc.release()
else:
    print('Association rejected, aborted or never connected')

print('done')