import os
import ssl
from pydicom.dataset import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import Verification
import pprint


# Function to handle C-ECHO requests
def handle_echo(event):
    print("echo request received")
    pprint.pprint(event)
    return 0x0000  # Success

aet = os.environ.get("DICOM_AET", "PYDICOM_WITH_TLS")
port = int(os.environ.get("DICOM_PORT", "11112"))
key_file = os.environ.get("PRIVATE_KEY", "/tls/pydicom-with-tls-key.pem")
cert_file = os.environ.get("CERTIFICATE", "/tls/pydicom-with-tls-crt.pem")
ignore_eof = int(os.environ.get("IGNORE_UNEXPECTED_EOF", "0")) == 1

ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
if ignore_eof:
    print("ignoring unexpected EOF")
    ssl_context.options |= ssl.OP_IGNORE_UNEXPECTED_EOF


# AE (Application Entity) setup
ae = AE(ae_title=aet.encode("utf-8"))
ae.require_calling_aet = []  # do not check calling AET
ae.require_called_aet = False # do not check called AET
ae.add_supported_context(Verification) # "1.2.840.10008.1.1", scp_role=True, scu_role=True)

# Add the C-ECHO SCP handler
handlers = [(evt.EVT_C_ECHO, handle_echo)]

# Start the SCP server
scp_server = ae.start_server(('0.0.0.0', port), block=False, ssl_context=ssl_context, evt_handlers=handlers)

print(f"server listening on port {port}")

# Main loop
try:
    while True:
        pass
except KeyboardInterrupt:
    ae.shutdown()
