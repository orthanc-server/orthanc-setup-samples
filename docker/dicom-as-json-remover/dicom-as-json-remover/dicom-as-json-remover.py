import boto3
import logging
import os
import dataclasses
import psycopg2
from orthanc_tools import Scheduler

logger = logging.getLogger('remover')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

pg_host = os.environ.get("PG_HOST")
pg_pwd = os.environ.get("PG_PWD")
pg_user = os.environ.get("PG_USER")
pg_db = os.environ.get("PG_DB")

runs_only_at_night = os.environ.get("RUNS_ONLY_AT_NIGHT", "true").lower() == "true"
is_pg_6 = os.environ.get("PG_PLUGIN_VERSION", "6") == "6"

is_s3_enabled = os.environ.get("ORTHANC__AWS_S3_STORAGE__ACCESS_KEY") is not None
root_path = "/var/lib/orthanc/db/"

@dataclasses.dataclass
class S3Configuration:
     aws_access_key_id: str
     aws_secret_access_key: str
     bucket: str
     endpoint: str = None

scheduler = Scheduler(night_start_hour=19, night_end_hour=7, run_only_at_night_and_weekend=runs_only_at_night)

if is_s3_enabled:
    s3_config = S3Configuration(aws_access_key_id=os.environ.get("ORTHANC__AWS_S3_STORAGE__ACCESS_KEY"),
                                aws_secret_access_key=os.environ.get("ORTHANC__AWS_S3_STORAGE__SECRET_KEY"),
                                bucket=os.environ.get("ORTHANC__AWS_S3_STORAGE__BUCKET_NAME"))

    s3 = boto3.client('s3',
                    aws_access_key_id=s3_config.aws_access_key_id,
                    aws_secret_access_key=s3_config.aws_secret_access_key,
                    endpoint_url=s3_config.endpoint)

def check_file_exists_in_s3(file_key):
    global s3, s3_config
    try:
        s3.head_object(Bucket=s3_config.bucket, Key=f"{file_key}.json")
        return True
    except Exception as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            # Handle other exceptions if needed
            raise

def check_file_exists_on_disk(file_key):
    path = f"{file_key[0:2]}/{file_key[2:4]}/{file_key}"
    return os.path.exists(os.path.join(root_path, path))

def delete_from_db(psql, uuid, id):
    global is_pg_6
    cur2 = psql.cursor()
    if is_pg_6:
        cur2.execute("SELECT * FROM CreateDeletedFilesTemporaryTable();")
    cur2.execute(f"DELETE FROM AttachedFiles WHERE id={id} AND uuid='{uuid}' AND fileType=2")
    psql.commit()
    cur2.close()

def delete_from_disk(file_key):
    try:
        path = f"{file_key[0:2]}/{file_key[2:4]}/{file_key}"
        os.remove(os.path.join(root_path, path))
    except Exception as e:
        print(f"failed to delete {file_key} from disk {e}")

def delete_from_s3(file_key):
    global s3, s3_config
    try:
        s3.delete_object(Bucket=s3_config.bucket, Key=f"{file_key}.json")
    except Exception as e:
        print(f"failed to delete {file_key} from s3 {e}")

psql = psycopg2.connect(host=pg_host, password=pg_pwd, user=pg_user, database=pg_db)

done = False
counter = 0
while not done:
    scheduler.wait_right_time_to_run()
    
    cur = psql.cursor()
    cur.execute("SELECT uuid, id FROM AttachedFiles WHERE fileType=2 ORDER BY id LIMIT 100;")
    records = cur.fetchall()
    cur.close()

    if len(records) == 0:
        break

    for record in records:
        uuid = record[0]
        id = record[1]
        if check_file_exists_on_disk(uuid):
            # print(f"{uuid}, {id} disk")
            delete_from_db(psql, uuid, id)
            delete_from_disk(uuid)
        elif is_s3_enabled and check_file_exists_in_s3(uuid):
            # print(f"{uuid}, {id} s3")
            delete_from_db(psql, uuid, id)
            delete_from_s3(uuid)
        else:
            print(f"{uuid}, {id} not found")

    counter += len(records)
    print(f"processed {counter} - {id}")

print("all files have been processed")