import psycopg2
import os
import typing
import pprint
from orthanc_api_client import OrthancApiClient

orthanc_url = os.environ.get("ORTHANC_URL", "http://localhost:8042")
orthanc_user = os.environ.get("ORTHANC_USER", "http://localhost:8042")
orthanc_pwd = os.environ.get("ORTHANC_PWD", "http://localhost:8042")
pg_host = os.environ.get("PG_HOST", "localhost")
pg_port = int(os.environ.get("PG_PORT", "5432"))
pg_user = os.environ.get("PG_USER", "postgres")
pg_pwd = os.environ.get("PG_PWD", "postgres")
pg_db_name = os.environ.get("PG_DATABASE", "postgres")
dev_mode = os.environ.get("DEV_MODE", "false") == "true"

conn = psycopg2.connect(
    dbname=pg_db_name,
    user=pg_user,
    password=pg_pwd,
    host=pg_host,
    port=pg_port
)


orthanc = OrthancApiClient(orthanc_root_url=orthanc_url,
                           user = orthanc_user,
                           pwd = orthanc_pwd)


def get_main_dicom_tags(internal_id) -> typing.Dict[str, str]:
    tags = {}
    cur = conn.cursor()

    sql_query = f"select taggroup, tagelement, value from maindicomtags where id = {internal_id};"
    cur.execute(sql_query)
    rows = cur.fetchall()
    for row in rows:
        tags[f"{row[0]:04x},{row[1]:04x}"] = row[2]

    cur.close()
    return tags


def check_patient(public_id, internal_ids):
    reference_tags = get_main_dicom_tags(internal_id=internal_ids[0])
    for internal_id in internal_ids:
        tags = get_main_dicom_tags(internal_id=internal_id)
        if tags != reference_tags:
            print(f"Patient {public_id}-{internal_id} has inconsistent MainDicomTags: ")

        sql_query = f"select internalid, publicid, resourcetype from resources where parentid = {internal_id};"
        cur.execute(sql_query)
        rows = cur.fetchall()

        print(f"Patient {public_id}-{internal_id} has {len(rows)} child studies")

    orthanc_patient = orthanc.patients.get(orthanc_id=public_id)
    print(f"Patient {public_id}-{internal_id} retrieved from Orthanc: {orthanc_patient.dicom_id}")

# find duplicate patients

cur = conn.cursor()


if dev_mode:  # return all patients
    sql_query = "select internalid, publicid, resourcetype from Resources where resourcetype = 0;"
else: # return only duplicate patients
    sql_query = "select internalid, publicid, resourcetype from Resources where publicid IN (select publicid from Resources where resourcetype = 0 group by publicid having COUNT(*)> 1);"

cur.execute(sql_query)

patients = {}
rows = cur.fetchall()

if len(rows) == 0:
    print("no duplicates")
else:
    for row in rows:
        internal_id = row[0]
        public_id = row[1]
        
        if not row[0] in patients:
            patients[public_id] = []
        patients[public_id].append(internal_id)

    for patient_public_id, patient_internal_ids in patients.items():
        print(f"Patient {patient_public_id} has {len(patient_internal_ids)} duplicates")
        check_patient(patient_public_id, patient_internal_ids)

cur.close()
conn.close()
