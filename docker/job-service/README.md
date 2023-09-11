# Purpose

This is a sample setup to demonstrate how to implement a `job-service` side container to centralize jobs management
when multiple Orthanc instances are running behind a load balancer.

In this setup, the `job-service` has no initial knowledge of the cluster topology but each Orthanc instance from the
cluster knows the `job-service`.

At startup or each time a job is updated, each Orthanc instance registers at the `job-service` that is then able to centralizes
the jobs, polls for progress report and forward job actions (e.g Cancel, Resume, ...) to the Orthanc instance owning the job.

This `job-service` only maintains an in memory DB of the jobs.  The DB is rebuilt everytime the service restarts.


# Description

This demo contains:

- 3 `orthanc` instances
- a `db` server to store that SQL Db shared between these 3 Orthanc instances
- a `job-service` that centralizes the job management for all 3 Orthanc instances.
- a `nginx` instance acting as a load-balancer in front of the 3 Orthanc instances and redirecting the `/jobs/` routes to the
  `job-service`

# Starting the setup

To start the setup, type: `docker-compose up --build --force-recreate`.

# demo

- open the Orthanc interface at [http://localhost/orthanc/ui/app/](http://localhost/orthanc/ui/app/) (login/pwd: `demo`/`demo`).  You'll notice that, if you
  refresh the page, you'll reach a different Orthanc instance (check the names in the OE2 UI)
- upload a study and download it, this is an easy way to create a job
- refresh the UI and repeat multiple times to have multiple jobs created on multiple Orthanc instances
- open the [http://localhost/orthanc/jobs?expand](http://localhost/orthanc/jobs?expand) route to show all jobs from all Orthanc instances.
- open the [http://localhost/orthanc/jobs?expand&status=Success](http://localhost/orthanc/jobs?expand&status=Success) route to show all jobs that have completed successfully.
- jobs status are refreshed every 5 seconds.  However, if you want to check the status of a specific job, you may call `http://localhost/orthanc/jobs/{id}` directly
- if you want to pause/cancel/resume a job, you may call e.g `http://localhost/orthanc/jobs/{id}/pause` directly
- each time an Orthanc leaves the cluster, its internal status will be marked as `STOPPED` (possibly as `NOT_RESPONDING` then `STOPPED` in case of hard switch-off).  However, right now, the `job-service` will still list the jobs from `STOPPED` Orthanc instances (this can be tuned in the `job-registry.py` file)

