from typing import Dict, List, Any
import json
import sqlite3
import requests

import logging
import enum
import threading
import time
import datetime


# reduce verbosity
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class OrthancException(BaseException):

    payload: Any = None
    status_code: int = None

    def __init__(self, status_code: int, payload: Any):
        self.payload = payload
        self.status_code = status_code


class OrthancStatus(enum.StrEnum):
    ALIVE = "alive"
    STOPPED = "stopped"
    NOT_RESPONDING = "not-responding"


class JobAction(enum.StrEnum):
    PAUSE = "pause"
    CANCEL = "cancel"
    RESUME = "resume"
    RESUBMIT = "resubmit"



class JobRegistry:

    db = None
    _update_thread = None
    not_responding_counter = {}
    not_responding_counter_lock = threading.Lock()
    api_tokens = {}
    api_tokens_lock = threading.Lock()


    def __init__(self) -> None:
        if sqlite3.threadsafety != 3:  # this should not happen with python 3.11
            raise Exception("Unable to use SQLite 3 with multiple threads")

        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        
        cursor = self.db.cursor()

        stmt = "CREATE TABLE IF NOT EXISTS orthanc_jobs(id TEXT PRIMARY KEY, orthanc_ip TEXT, job_status TEXT, orthanc_status TEXT, content TEXT)"
        cursor.execute(stmt)
        cursor.close()
        self.db.commit()

        # launch a thread to poll jobs status from all Orthanc instances every N seconds
        self._update_thread = threading.Thread(target=self._update_thread, args=(5, ))
        self._update_thread.start()


    # returns headers required to authenticate into Orthanc
    def get_orthanc_headers(self, orthanc_ip: str):

        with self.api_tokens_lock:
            return {
                "Authorization": self.api_tokens[orthanc_ip]
            }


    # records that a new Orthanc instance has been started
    def orthanc_started(self, orthanc_ip: str, api_token: str):
        logging.info(f"An Orthanc has started with IP {orthanc_ip}")

        self._update_api_token(orthanc_ip=orthanc_ip, api_token=api_token)

        self.update_orthanc_jobs(orthanc_ip=orthanc_ip)

    def _update_api_token(self, orthanc_ip: str, api_token: str):
        with self.api_tokens_lock:
            self.api_tokens[orthanc_ip] = api_token


    # updates the orthanc status of all jobs belonging to an Orthanc instance
    def _update_orthanc_status(self, orthanc_ip, orthanc_status):
        cursor = self.db.cursor()

        stmt = "UPDATE orthanc_jobs SET orthanc_status = :orthanc_status WHERE orthanc_ip = :orthanc_ip"
        cursor.execute(stmt, {
            'orthanc_status': orthanc_status,
            'orthanc_ip': orthanc_ip
            })
        self.db.commit()


    # records that an Orthanc instance has been stopped
    def orthanc_stopped(self, orthanc_ip):
        logging.info(f"The Orthanc whose IP is {orthanc_ip} is stopping")

        self._update_orthanc_status(orthanc_ip=orthanc_ip, orthanc_status=OrthancStatus.STOPPED)


    # refreshes all jobs from all Orthanc instances
    def refresh_all_jobs(self):
        cursor = self.db.cursor()
        stmt = "SELECT DISTINCT orthanc_ip FROM orthanc_jobs WHERE orthanc_status IN (:status1, :status2)"
        rows = cursor.execute(stmt, {
            'status1': OrthancStatus.ALIVE,
            'status2': OrthancStatus.NOT_RESPONDING
            })

        rows = rows.fetchall()
        for row in rows:
            orthanc_ip = row[0]

            is_responding = self.update_orthanc_jobs(orthanc_ip=orthanc_ip)

            with self.not_responding_counter_lock:
                if orthanc_ip not in self.not_responding_counter:
                    self.not_responding_counter[orthanc_ip] = 0

                if not is_responding:
                    self.not_responding_counter[orthanc_ip] += 1
                    if self.not_responding_counter[orthanc_ip] > 5:
                        logging.error(f"Orthanc {orthanc_ip} has not responded for a while, considering it as stopped")
                        self._update_orthanc_status(orthanc_ip=orthanc_ip, orthanc_status=OrthancStatus.STOPPED)
                else:
                    self.not_responding_counter[orthanc_ip] = 0


    # polls all jobs from all Orthanc instances at regular interval
    def _update_thread(self, interval: float):
        last_run = datetime.datetime.now()

        while True:
            next_run = last_run + datetime.timedelta(seconds=interval)
            if next_run > last_run:
                time.sleep((next_run - last_run).total_seconds())
            self.refresh_all_jobs()

            last_run = datetime.datetime.now()


    # updates all jobs from a single Orthanc instance
    def update_orthanc_jobs(self, orthanc_ip) -> bool:
        logging.info(f"Updating all jobs status for Orthanc IP {orthanc_ip}")

        try:
            jobs = requests.get(f"http://{orthanc_ip}:8042/jobs?expand", headers=self.get_orthanc_headers(orthanc_ip=orthanc_ip)).json()
        except Exception as ex:
            logging.error(f"Failed to update orthanc jobs for {orthanc_ip}, setting orthanc_status to NOT_RESPONDING")
            self._update_orthanc_status(orthanc_ip=orthanc_ip, orthanc_status=OrthancStatus.NOT_RESPONDING)
            return False

        cursor = self.db.cursor()

        stmt = "DELETE FROM orthanc_jobs WHERE orthanc_ip=:ip"
        cursor.execute(stmt, {'ip': orthanc_ip})

        for job in jobs:
            self._insert_job(cursor=cursor, orthanc_ip=orthanc_ip, job=job)

        self.db.commit()
        return True


    # inserts a job in DB (internal)
    def _insert_job(self, cursor, orthanc_ip, job):
        stmt = "INSERT INTO orthanc_jobs (id, orthanc_ip, job_status, orthanc_status, content)  VALUES(:id, :orthanc_ip, :job_status, :orthanc_status, :content)"

        cursor.execute(stmt, {
            "id": job["ID"],
            "orthanc_ip": orthanc_ip,
            "job_status": job["State"],
            "orthanc_status": OrthancStatus.ALIVE,
            "content": json.dumps(job)
            })


    # updates a job in DB (internal)
    def _update_job(self, orthanc_ip, job):

        cursor = self.db.cursor()

        stmt = "DELETE FROM orthanc_jobs WHERE id=:id"
        cursor.execute(stmt, {'id': job["ID"]})

        self._insert_job(cursor=cursor, orthanc_ip=orthanc_ip, job=job)
        self.db.commit()


    # updates a job in DB
    # in case we have not received the "ORTHANC_STARTED" event, we receive the api-token now
    def update_job(self, orthanc_ip: str, job: str, api_token: str):
        
        job_id = job['ID']
        logging.info(f"A job {job_id} has been updated on Orthanc IP {orthanc_ip}")

        self._update_api_token(orthanc_ip=orthanc_ip, api_token=api_token)

        self._update_job(orthanc_ip=orthanc_ip, job=job)


    # gets all jobs from all Orthanc instances, possibly filtered by status
    def get_jobs(self, filter_status: str | None = None, expand: bool = False):

        cursor = self.db.cursor()

        # TODO: you may want to customize filtering here not to report the jobs from Orthanc that have been stopped
        if filter_status is not None:
            stmt = "SELECT content FROM orthanc_jobs WHERE job_status=:job_status"
            rows = cursor.execute(stmt, {'job_status': filter_status})
        else:
            stmt = "SELECT content FROM orthanc_jobs"
            rows = cursor.execute(stmt)

        jobs = []
        for row in rows:
            job = json.loads(row[0])
            if expand:
                jobs.append(job)
            else:
                jobs.append(job["ID"])
        
        return jobs


    # retrieves, from DB, the Orthanc instance that is the owner of a job
    def _get_job_orthanc_ip(self, job_id: str):
        cursor = self.db.cursor()

        stmt = "SELECT orthanc_ip FROM orthanc_jobs WHERE id=:job_id"
        rows = cursor.execute(stmt, {'job_id': job_id})

        rows = rows.fetchall()
        if len(rows) != 1:
            raise FileNotFoundError()

        orthanc_ip = rows[0][0]
        return orthanc_ip


    # gets the latest status of a job from the Orthanc instance owning that job
    def get_job(self, job_id: str):
        orthanc_ip = self._get_job_orthanc_ip(job_id=job_id)

        job = requests.get(f"http://{orthanc_ip}:8042/jobs/{job_id}", headers=self.get_orthanc_headers(orthanc_ip=orthanc_ip)).json()

        cursor = self.db.cursor()
        self._insert_job(cursor=cursor, orthanc_ip=orthanc_ip, job=job)

        self.db.commit()

        return job


    # forwards a job "action" to the Orthanc instance owning that job
    def post_job_action(self, job_id: str, job_action: JobAction):
        orthanc_ip = self._get_job_orthanc_ip(job_id=job_id)

        r = requests.post(f"http://{orthanc_ip}:8042/jobs/{job_id}/{job_action}", headers=self.get_orthanc_headers(orthanc_ip=orthanc_ip))
        if r.status_code != 200:
            payload = None
            if len(r.content) > 0:
                payload = json.loads(r.content)
            raise OrthancException(status_code=r.status_code, payload=payload)
        else:
            return r.json()
            
