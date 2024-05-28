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

def check_instance(instance_uid, instances):  # instances = [(instance_public_id, instance_internal_id), ...]

    reference_instance_internal_id = instances[0][1]
    reference_instance_public_id = instances[0][0]
    reference_instance_tags = get_main_dicom_tags(internal_id=reference_instance_internal_id)
    duplicates_to_delete = [x[1] for x in instances[1:]]
    str_duplicates_to_delete = ', '.join([str(x) for x in duplicates_to_delete])
    # series_internal_ids = [x[1] for x in series]
    # str_series_internal_ids = ', '.join([str(x) for x in series_internal_ids])

    all_instances_duplicates_are_identical = True
    for (instance_public_id, instance_internal_id) in instances:
        tags = get_main_dicom_tags(internal_id=instance_internal_id)
        if tags != reference_instance_tags:
            all_instances_duplicates_are_identical = False
            print(f"..Instance {instance_public_id}/{instance_internal_id} has inconsistent MainDicomTags")
            print_diff_tags(reference_instance_tags, reference_instance_internal_id, tags, instance_internal_id)


    if all_instances_duplicates_are_identical:
        if len(duplicates_to_delete) > 0:
            print(f"All instances duplicates are identical, it is safe to delete redundant instances {str_duplicates_to_delete}")
            # now that the duplicates do not have any childs anymore, it is safe to delete them from resources -> this will also delete MainDicomTags, DicomIdentifiers, Metadata, AttachedFiles, Changes, PatientRecyclingOrder, Labels
            print(f"TODO delete from Resources where internalid in ({str_duplicates_to_delete})")
        else:
            print(f"This instance does not have duplicates anymore")
    else:
        print(f"Can not merge instances")


def check_series(series_uid, series):  # series = [(series_public_id, series_internal_id), ...]

    reference_series_internal_id = series[0][1]
    reference_series_public_id = series[0][0]
    reference_series_tags = get_main_dicom_tags(internal_id=reference_series_internal_id)
    duplicates_to_delete = [x[1] for x in series[1:]]
    str_duplicates_to_delete = ', '.join([str(x) for x in duplicates_to_delete])
    series_internal_ids = [x[1] for x in series]
    str_series_internal_ids = ', '.join([str(x) for x in series_internal_ids])

    orthanc_series = orthanc.series.get(orthanc_id=reference_series_public_id)
    print(f"..Series {reference_series_public_id}/{reference_series_internal_id} retrieved from Orthanc: {orthanc_series.dicom_id}")

    all_series_duplicates_are_identical = True
    for (series_public_id, series_internal_id) in series:
        tags = get_main_dicom_tags(internal_id=series_internal_id)
        if tags != reference_series_tags:
            all_series_duplicates_are_identical = False
            print(f"..Series {series_public_id}/{series_internal_id} has inconsistent MainDicomTags")
            print_diff_tags(reference_series_tags, reference_series_internal_id, tags, series_internal_id)

    if all_series_duplicates_are_identical:
        if len(duplicates_to_delete) > 0:
            print(f"All series duplicates are identical, it is safe to merge {str_duplicates_to_delete} into {reference_series_internal_id}")
            # replace the instances' parent by the reference one
            print(f"TODO update set parentid = {reference_series_internal_id} from resources where parentid in ({str_duplicates_to_delete})")
            # now that the duplicates do not have any childs anymore, it is safe to delete them from resources -> this will also delete MainDicomTags, DicomIdentifiers, Metadata, AttachedFiles, Changes, PatientRecyclingOrder, Labels
            print(f"TODO delete from Resources where internalid in ({str_duplicates_to_delete})")
        else:
            print(f"This series does not have duplicates anymore")
    else:
        print(f"Can not merge series")

    sql_query = f"select internalid, publicid, resourcetype from resources where parentid in ({str_series_internal_ids});"
    cur.execute(sql_query)
    rows = cur.fetchall()
    print(f"..Series {reference_series_public_id}/{reference_series_internal_id} has {len(rows)} child instances")

    instances_by_uid = {}
    for row in rows:
        instance_internal_id = row[0]
        instance_public_id = row[1]

        instance_tags = get_main_dicom_tags(internal_id=instance_internal_id)
        instance_uid = instance_tags["0008,0018"]
        if instance_uid not in instances_by_uid:
            instances_by_uid[instance_uid] = []
        instances_by_uid[instance_uid].append((instance_public_id, instance_internal_id))

    for (instance_uid, instances) in instances_by_uid.items():
        print(f"..Analyzing {len(instances)} child instances of Series {reference_series_public_id}/{reference_series_internal_id} with the same SOPInstanceUID {instance_uid}")
        check_instance(instance_uid, instances)



def check_study(study_uid, studies):  # studies = [(study_public_id, study_internal_id), ...]

    reference_study_internal_id = studies[0][1]
    reference_study_public_id = studies[0][0]
    reference_study_tags = get_main_dicom_tags(internal_id=reference_study_internal_id)
    duplicates_to_delete = [x[1] for x in studies[1:]]
    str_duplicates_to_delete = ', '.join([str(x) for x in duplicates_to_delete])
    study_internal_ids = [x[1] for x in studies]
    str_study_internal_ids = ', '.join([str(x) for x in study_internal_ids])


    orthanc_study = orthanc.studies.get(orthanc_id=reference_study_public_id)
    print(f".Study {reference_study_public_id}/{reference_study_internal_id} retrieved from Orthanc: {orthanc_study.dicom_id}")

    all_studies_duplicates_are_identical = True
    for (study_public_id, study_internal_id) in studies:
        tags = get_main_dicom_tags(internal_id=study_internal_id)
        if tags != reference_study_tags:
            all_studies_duplicates_are_identical = False
            print(f".Study {study_public_id}/{study_internal_id} has inconsistent MainDicomTags")
            print_diff_tags(reference_study_tags, reference_study_internal_id, tags, study_internal_id)

    if all_studies_duplicates_are_identical:
        if len(duplicates_to_delete) > 0:
            print(f"All studies duplicates are identical, it is safe to merge {str_duplicates_to_delete} into {reference_study_internal_id}")
            # replace the series' parent by the reference one
            print(f"TODO update set parentid = {reference_study_internal_id} from resources where parentid in ({str_duplicates_to_delete})")
            # now that the duplicates do not have any childs anymore, it is safe to delete them from resources -> this will also delete MainDicomTags, DicomIdentifiers, Metadata, AttachedFiles, Changes, PatientRecyclingOrder, Labels
            print(f"TODO delete from Resources where internalid in ({str_duplicates_to_delete})")
        else:
            print(f"This study does not have duplicates anymore")
    else:
        print(f"Can not merge studies")


    sql_query = f"select internalid, publicid, resourcetype from resources where parentid in ({str_study_internal_ids});"
    cur.execute(sql_query)
    rows = cur.fetchall()
    print(f".Study {reference_study_public_id}/{reference_study_internal_id} has {len(rows)} child series")

    series_by_uid = {}
    for row in rows:
        series_internal_id = row[0]
        series_public_id = row[1]
        # orthanc_series = orthanc.series.get(orthanc_id=series_public_id)
        # print(f"..Child series {series_public_id}/{series_internal_id} has {len(orthanc_series.instances)} instances, SeriesInstanceUID {orthanc_series.dicom_id}")

        series_tags = get_main_dicom_tags(internal_id=series_internal_id)
        series_uid = series_tags["0020,000e"]
        if series_uid not in series_by_uid:
            series_by_uid[series_uid] = []
        series_by_uid[series_uid].append((series_public_id, series_internal_id))

    for (series_uid, series) in series_by_uid.items():
        print(f".Analyzing {len(series)} child series of Study {reference_study_public_id}/{reference_study_internal_id} with the same SeriesInstanceUID {series_uid}")
        check_series(series_uid, series)



def check_patient(public_id, patient_internal_ids):
    reference_internal_id = patient_internal_ids[0]
    duplicates_to_delete = patient_internal_ids[1:]
    str_duplicates_to_delete = ', '.join([str(x) for x in duplicates_to_delete])
    str_patient_internal_ids = ', '.join([str(x) for x in patient_internal_ids])

    orthanc_patient = orthanc.patients.get(orthanc_id=public_id)
    print(f"Patient {public_id}/{reference_internal_id} retrieved from Orthanc: {orthanc_patient.dicom_id}")

    reference_tags = get_main_dicom_tags(internal_id=reference_internal_id)

    all_patient_duplicates_are_identical = True
    for internal_id in patient_internal_ids:
        tags = get_main_dicom_tags(internal_id=internal_id)
        if tags != reference_tags:
            print(f"Patient {public_id}/{internal_id} has inconsistent MainDicomTags: ")
            all_patient_duplicates_are_identical = False
            print_diff_tags(reference_tags, reference_internal_id, tags, internal_id)

    if all_patient_duplicates_are_identical:
        if len(duplicates_to_delete) > 0:
            print(f"All patient duplicates are identical, it is safe to merge {str_duplicates_to_delete} into {reference_internal_id}")
            # replace the studies' parent by the reference one
            print(f"TODO update set parentid = {reference_internal_id} from resources where parentid in ({str_duplicates_to_delete})")
            # now that the duplicates do not have any childs anymore, it is safe to delete them from resources -> this will also delete MainDicomTags, DicomIdentifiers, Metadata, AttachedFiles, Changes, PatientRecyclingOrder, Labels
            print(f"TODO delete from Resources where internalid in ({str_duplicates_to_delete})")
        else:
            print(f"This patient does not have duplicates anymore")
    else:
        print(f"Can not merge patients")
        exit(-1)

    sql_query = f"select internalid, publicid, resourcetype from resources where parentid in ({str_patient_internal_ids});"
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


cur = conn.cursor()

# First show all duplicates
for it in [('Patients', 0), ('Studies', 1), ('Series', 2), ('Instances', 3)]:
    type_str = it[0]
    type_id = it[1]
    sql_query = f"select internalid, publicid, resourcetype from Resources where publicid IN (select publicid from Resources where resourcetype = {type_id} group by publicid having COUNT(*)> 1);"
    cur.execute(sql_query)

    rows = cur.fetchall()
    print(f"Found {len(rows)} duplicate {type_str}")
    for row in rows:
        print(f"Duplicate {type_str} {row[1]}/{row[0]}")


# find duplicate patients
if dev_mode:  # return all patients
    sql_query = "select internalid, publicid, resourcetype from Resources where resourcetype = 0;"
else: # return only duplicate patients
    sql_query = "select internalid, publicid, resourcetype from Resources where publicid IN (select publicid from Resources where resourcetype = 0 group by publicid having COUNT(*)> 1);"
cur.execute(sql_query)

patients = {}
rows = cur.fetchall()

if len(rows) == 0:
    print("no patients duplicates")
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
