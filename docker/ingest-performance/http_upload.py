from pydicom import dcmread

import requests
import os
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--http_port', type=int, default=9042)
parser.add_argument('--folder', type=str, default="/mnt/c/Users/Alain/o/dicom-files/store-scu/files/thorax-ct-1")
args = parser.parse_args()

root_folder = args.folder

for path in glob.glob(os.path.join(root_folder, '**/*.dcm')):

    with open(path, "rb") as f:
        content = f.read()

    r = requests.post(f'http://localhost:{args.http_port}/instances', data = content)
    if r.status_code != 200:
        print('Error')

print('done')