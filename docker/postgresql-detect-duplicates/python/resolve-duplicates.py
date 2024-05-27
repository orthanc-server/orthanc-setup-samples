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

def print_diff_tags(reference_tags, reference_tags_id, tags, tags_id):
    all_keys = set(tags.keys()).union(set(reference_tags.keys()))
    for k in all_keys:
        if k not in reference_tags:
            print(f"Diff: {k} missing from reference_tags {reference_tags_id}")
        elif k not in tags:
            print(f"Diff: {k} missing from tags {tags_id}")
        elif reference_tags[k] != tags[k]:
            print(f"Diff: {k} values differ: {reference_tags[k]}/{tags[k]} --- {reference_tags_id}/{tags_id}")
            

def check_study(study_uid, studies):  # studies = [(study_public_id, study_internal_id), ...]

    reference_study_internal_id = studies[0][1]
    reference_study_tags = get_main_dicom_tags(internal_id=reference_study_internal_id)
    
    for (study_public_id, study_internal_id) in studies:
        orthanc_study = orthanc.studies.get(orthanc_id=study_public_id)
        print(f".Study {study_public_id}/{study_internal_id} retrieved from Orthanc: {orthanc_study.dicom_id}")

        tags = get_main_dicom_tags(internal_id=study_internal_id)
        if tags != reference_study_tags:
            print(f".Study {study_public_id}/{study_internal_id} has inconsistent MainDicomTags")
            print_diff_tags(reference_study_tags, studies[0][1], tags, study_internal_id)

        sql_query = f"select internalid, publicid, resourcetype from resources where parentid = {study_internal_id};"
        cur.execute(sql_query)
        rows = cur.fetchall()
        print(f".Study {study_public_id}/{study_internal_id} has {len(rows)} child series")

        for row in rows:
            series_internal_id = row[0]
            series_public_id = row[1]
            orthanc_series = orthanc.series.get(orthanc_id=series_public_id)
            print(f"..Child series {series_public_id}/{series_internal_id} has {len(orthanc_series.instances)} instances, SeriesInstanceUID {orthanc_series.dicom_id}")



def check_patient(public_id, internal_ids):
    reference_internal_id = internal_ids[0]
    duplicates_to_delete = internal_ids[1:]

    orthanc_patient = orthanc.patients.get(orthanc_id=public_id)
    print(f"Patient {public_id}/{reference_internal_id} retrieved from Orthanc: {orthanc_patient.dicom_id}")

    reference_tags = get_main_dicom_tags(internal_id=reference_internal_id)

    all_patient_duplicates_are_identical = True
    for internal_id in internal_ids:
        tags = get_main_dicom_tags(internal_id=internal_id)
        if tags != reference_tags:
            print(f"Patient {public_id}/{internal_id} has inconsistent MainDicomTags: ")
            all_patient_duplicates_are_identical = False
            print_diff_tags(reference_tags, reference_internal_id, tags, internal_id)

    if all_patient_duplicates_are_identical:
        print(f"All patient duplicates are identical, it is safe to merge {', '.join(duplicates_to_delete)} into {reference_internal_id}")
        # replace the studies' parent by the reference one
        print(f"TODO update set parentid = {reference_internal_id} from resources where parentid in ({', '.join(duplicates_to_delete)})")
        # now that the duplicates do not have any childs anymore, it is safe to delete them from resources -> this will also delete MainDicomTags, DicomIdentifiers, Metadata, AttachedFiles, Changes, PatientRecyclingOrder, Labels
        print(f"TODO delete from Resources where internalid in ({', '.join(duplicates_to_delete)})")


    sql_query = f"select internalid, publicid, resourcetype from resources where parentid = {reference_internal_id};"
    cur.execute(sql_query)
    rows = cur.fetchall()

    if len(rows) == 1:
        print(f"Patient {public_id}/{reference_internal_id} has 1 child study {rows[0][1]}/{rows[0][0]}")
    else:
        print(f"Patient {public_id}/{reference_internal_id} has multiple child studies {len(rows)}")

    studies_by_uid = {}
    for row in rows:
        study_internal_id = row[0]
        study_public_id = row[1]

        tags = get_main_dicom_tags(internal_id=study_internal_id)
        study_uid = tags["0020,000d"]
        if study_uid not in studies_by_uid:
            studies_by_uid[study_uid] = []
        studies_by_uid[study_uid].append((study_public_id, study_internal_id))

    for (study_uid, studies) in studies_by_uid.items():
        print(f"Analyzing {len(studies)} child studies of Patient {public_id}/{reference_internal_id} with the same StudyInstanceUID {study_uid}")
        check_study(study_uid, studies)




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
        
        if not public_id in patients:
            patients[public_id] = []
        patients[public_id].append(internal_id)

    for patient_public_id, patient_internal_ids in patients.items():
        print(f"Patient {patient_public_id} has {len(patient_internal_ids)} duplicates")
        check_patient(patient_public_id, patient_internal_ids)

cur.close()
conn.close()
