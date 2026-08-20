# Purpose

This is a sample setup to demonstrate how to implement a custom python storage plugin that
zips series before uploading them into S3.

In the setup, we do introduce an artificial latency between Orthanc and the S3 plugin to
demonstrate how the S3-Zip plugin helps improve upload/download time on a system with a 
large latency.

# Description

To run the setup:

```
docker pull orthancteam/orthanc-pre-release:master-unstable
uv run ./tests/test_scenario.py
```

The test scenario:
- starts the `docker-compose` setup
- performs some functional REST Api tests
- uploads a test study on 2 Orthanc instances:
  - one with the standard S3 plugin (`s3-default`)
  - one with the S3-Zip python plugin (`s3-zip`)
- cleanup the S3-Zip plugin local storage
- restarts the system to clear the storage caches
- download the studies again

## The `.s3-uploaded` marker

The local folder of a series is deleted by the eviction pass only if it holds
an `.s3-uploaded` marker. That marker is a single, load-bearing claim:

> every instance file in this folder can be read back from the S3 zip named
> inside it.

Two rules keep the claim true, and both exist because breaking either one
destroys DICOM data:

1. **The marker is published against the DISK, never against Orthanc's
   index.** Orthanc calls the storage area's `Create` *before* it commits the
   attachment row, so a brand-new instance is on disk while `/tools/find`
   still reports the previous attachment set. A copy that asks the index
   "anything new?" gets told "no" and publishes a marker that covers a file
   the zip does not contain — the next eviction then deletes the only copy of
   that instance. `copy_series_to_s3` therefore lists the folder and withholds
   the marker if it holds anything the uploaded zip does not.

2. **`storage_create` holds the folder lease across both the write and the
   marker invalidation.** A folder that is already on S3 carries a marker; the
   instance being added is not in that zip. Between the file landing and the
   marker being wiped, the folder is a legal eviction target holding data that
   exists nowhere else. The lease makes the eviction pass skip it for the
   duration.

Running out of local space is a designed-for state, not an edge case: folders
awaiting their upload are protected, so a cache under pressure legitimately
has nothing to evict. The budget is a target rather than a wall — writes are
admitted past it, and the filesystem is the hard limit (an `ENOSPC` write
fails the C-STORE, which is what makes the modality retry).

## `GET /series/<id>/archive` is deliberately NOT overridden

The plugin used to override this one route and forward the stored S3 zip to
the client byte for byte, but the files lacked the `.dcm` extension. We prefer 
to let the Orthanc core build the archive, by reading every instance and 
assembling the archive with proper file extensions.

The override is gone. The route falls through to the Orthanc core, which
builds the archive the same way it builds study- and patient-level archives:
it reads the **current** attachment list, one instance at a time, through this
plugin's `storage_read_range`.

Why that is safe against everything eviction, retrieval, ingestion and
deletion can do concurrently:

* **Each read leases the folder from the existence check through the read**,
  and retrieval leases it during extraction, so the eviction pass can never
  delete a folder out from under either. Leases are shared counters, not
  locks — concurrent readers do not block each other, and the nesting
  (read → retrieval) is just two increments.
* **Between two instance reads there is a gap** in which an eviction pass may
  legitimately take the folder (it carries a marker the moment retrieval
  proves the folder matches the zip). The next read simply rehydrates again.
  Under adversarial eviction pressure that costs extra downloads — never
  correctness. One of the host applications for this plugin complete-e2e test
  hammers eviction every 2 seconds during processing and downloads correct 
  archives throughout.
* **A new instance arriving mid-archive cannot be evicted into oblivion**:
  `storage_create` writes the file and invalidates the marker under the
  per-folder critical section, and retrieval republishes the marker only if
  the folder exactly matches the extracted zip. A folder holding anything not
  yet in a zip is not evictable, so the core always finds fresh instances on
  local disk. (Whether a mid-build instance appears in the archive is decided
  by the core's own snapshot of the instance list, as on any storage backend.)
* **Concurrent archive requests for the same cold series** trigger one
  retrieval, not N: retrievals are single-flighted per zip key, and waiters
  share the outcome, including a terminal failure.
* **Failures are loud.** If the zip cannot be fetched (S3 down, object
  deleted by the housekeeper after a study deletion, corrupt download), the
  read returns an error and the archive request fails — the core never serves
  a partial zip that looks whole. A series quarantined with lost data fails
  its archive request the same way, instead of the override's old behaviour
  of serving the last complete zip as if nothing were missing.

The price, accepted knowingly: a cold-cache series download now costs a
rehydration (zip download, full extraction into the cache, per-instance
reads, re-zip) instead of a cache-neutral stream from S3, and it occupies
cache until eviction reclaims it. Warm-cache downloads get cheaper — they no
longer touch S3 at all. If bulk cold series export ever becomes a dominant
workload, resurrect the override *with a re-pack* (rename members to
`<uuid>.dcm` on the way out) rather than as a verbatim forward.

# TODO

## Making sure all series are uploaded to S3

### Problem

The plugin's durability story relies on the `uncommitted-series` KVS as the
single source of truth for "which series have not yet been zipped to S3".
The KVS is populated by the `on_new_series` handler (NEW_SERIES change
event) and cleared by `on_committed_series` (after a successful S3 upload).

The runtime housekeeper consumes the KVS, finds entries older than
`_UNCOMMITTED_MIN_AGE_SEC`, and routes each through the three-branch
decision tree (all / partial / no local data).

The KVS is backed by Orthanc's PostgreSQL metadata store, so entries
written in one pod lifetime survive into the next. This is what makes
recovery work in the common case: a pod dies between NEW_SERIES and
STABLE_SERIES, the next pod starts, and the housekeeper finds the lingering
KVS entry.

However, the source-of-truth model has three residual gaps:

1. **`on_new_series` KVS write failure.** The handler catches and logs the
   exception, then returns without re-raising (see the comment in
   `uncommitted_series_handler.on_new_series`). If the write fails for any
   reason — transient PG hiccup, plugin reload mid-event, container under
   memory pressure — there is no KVS entry. The series is invisible to the
   housekeeper. STABLE_SERIES may still fire later and schedule the copy,
   but if the pod dies before STABLE_SERIES, the series is permanently
   orphaned.

2. **Race between `storage_create` and the NEW_SERIES dispatch.** Orthanc
   writes the attachment to local disk (and the index record to PG) in the
   C-STORE thread; the change-event handlers run afterwards. A pod death
   between these two points (kernel OOM kill, spot eviction) leaves the
   instance on disk + recorded in the index, with no NEW_SERIES having
   fired on either side of the restart — Orthanc does not replay change
   events on startup. The series exists, has local-only attachments, and
   the KVS-driven housekeeper cannot see it.

3. **Pre-plugin history.** Any series that landed during a window when the
   s3zip plugin was not loaded (initial deployment before plugin enable, a
   plugin disable, an Orthanc-only restart with the Python plugin failing
   to load) has no KVS entry. The current mechanism cannot recover these.

The eviction loop is the failure mode. `LocalStorage._make_room()` protects
folders without the `.s3-uploaded` marker, so an orphaned series will not
be evicted while disk has room — but on a busy box, the LRU eventually
hits the "no safely-evictable folder" branch, logs a WARNING, and evicts
anyway. The orphan is lost.

### Proposed solution

A two-part fix, in priority order:

**1. Move the KVS write from `on_new_series` down to `storage_create`.**

`storage_create` is the lowest-level hook in the storage backend — every
locally-written attachment passes through it, and it already performs a PG
round-trip to record the attachment. Adding the `uncommitted-series` KVS
write there (keyed by the series ID derived from the instance metadata)
closes gaps 1 and 2 in one stroke: there is no longer a window between
"file on disk" and "KVS entry written", and a swallowed exception in
`on_new_series` no longer matters because the KVS entry was already
written one layer down.

The cost is one extra PG round-trip per instance write. In practice this
is a write to the same PG instance that just recorded the attachment, so
the latency impact on the C-STORE hot path is bounded.

**2. Add a slow-cadence "all-series sweep" to the housekeeper.**

This is the belt-and-suspenders pass that closes gap 3 and serves as a
failsafe for anything else the KVS approach might miss. The mechanism:

- When the copy thread successfully uploads a series, set an Orthanc
  metadata tag on the series (proposed: `S3ZipDurable=<epoch_ms>`).
- Once per long interval (proposed: hourly, configurable; not per
  housekeeper tick), enumerate series **without** the `S3ZipDurable`
  metadata via `/tools/find`. Orthanc indexes metadata lookups in PG, so
  this is a single bounded query rather than an O(N) scan of all series.
- Feed each result into the existing three-branch decision tree
  (`_housekeep_one_uncommitted_series`).

This pass also picks up `S3ZipDataLost` / `S3ZipDataTainted` candidates
naturally: a series in either of those states is also "not durable" and
should appear in the same enumeration. The three values
(`S3ZipDurable`, `S3ZipDataLost`, `S3ZipDataTainted`) are three
mutually-exclusive states of the same "durability" field; they should be
designed as a set rather than independently. See the TODO comments in
`_housekeep_one_uncommitted_series` and `copy_series_to_s3` for the
related operator-enumerability work.

### Why not `/changes` replay

A startup-time `/changes` consumer (persist a cursor, replay missed
NEW_SERIES events on boot) was considered as a third option. It closes
fewer gaps than `storage_create` + all-series sweep:

- It does not close the `storage_create`-vs-NEW_SERIES race (the event
  was never recorded in `/changes` either).
- Cursor loss requires a full rescan anyway.
- Orthanc trims `/changes` past a configurable size; a long-dead pod can
  come back to find the relevant slice already gone.

The combination of `storage_create` and the all-series sweep dominates
`/changes` on every dimension that matters here, so `/changes` is not
proposed.

## Reporting and cleaning up series whose data was lost

### Problem

When a pod dies, its local storage dies with it. A series that had been
fully written locally but not yet copied to S3 comes back after the restart
as Orthanc index records with **no bytes behind them**.

The housekeeper detects this (branch 3 of the rescue tree) and schedules a
copy; the copy thread's guard logs an ERROR, acknowledges without
re-enqueueing, and clears the `uncommitted-series` KVS entry. So the
*bookkeeping* terminates correctly — a lost series costs one probe and then
never comes back. No KVS grows, and the housekeeper does not accumulate work.

What does accumulate is the **broken Orthanc records**. They:

- can never be read (every `storage_read_range` fails),
- can never be processed (processing waits for the study to be safe on S3),
- count against patient/study limits (e.g. `MaximumPatientCount`) and PG
  index size.

They are, however, **repairable**: re-sending the study fixes it, provided the
host Orthanc runs with `"OverwriteInstances": true` (the Gap Server does, in
every deployment; note that Orthanc's own default is `false`, in which case the
re-sent instance would be discarded as `AlreadyStored` and the broken record
would be unrecoverable until deleted). With overwriting enabled, the incoming
file replaces the stored one, `storage_create` writes fresh bytes, and the
series goes through the normal copy-to-S3 path again. `storage_remove` on the
vanished local file is caught and still returns SUCCESS, so it does not block
the overwrite.

So the remedy is simple. What is missing is that **nobody is ever told**: the
only trace of a data loss used to be a single ERROR line in the pod's log —
and in the CI run that motivated this section, that log had rotated before
anyone read it. Whoever could re-send the study has no way to learn that they
should.

### What exists today

A first, passive step is in place: a series that loses an attachment is
recorded in the `s3zip-series-with-lost-data` key-value store (series id,
count, the uuids, a timestamp), and the per-series status endpoint reports it:

```
GET /series/<id>/s3-zip/status
{ "is-stored-in-s3": true, "s3-zip-key": "...",
  "has-lost-data": true, "lost-attachment-count": 1 }
```

This matters because `is-stored-in-s3` alone cannot answer it: that flag is
read from **one** attachment's custom data, and the attachment whose bytes were
destroyed is exactly the one that keeps its `local` custom data while all its
siblings move to `s3-zip`. A mutilated series therefore reports itself as
stored. The KVS is the O(1) answer to the part sampling cannot see, and it
makes losses enumerable instead of grep-able.

A series that has lost an instance is **quarantined, not patched up**. One
unrecoverable attachment abandons the whole copy: nothing is uploaded, no
marker is published, and no attachment is told it lives in S3. This is
deliberate and it is a clinical judgement rather than a technical one — an
archive that silently omits an instance is worse than no archive at all,
because every consumer downstream would treat it as the series. The surviving
instances stay on local disk (they are the only copy left of themselves) and
the folder stays ineligible for eviction; cache space is the cheaper thing to
lose.

What the quarantine *does* fix is the collateral damage. The failing copy used
to be re-enqueued forever, and its retry backoff — up to 30 s — was slept on
the single shared copy worker, so one sick series held up every other series'
upload. In the run that motivated this, one destroyed instance kept 46
perfectly good ones out of S3 and pinned 15 MB of cache no eviction pass could
reclaim. The damage is now recorded once, the queue entry is released so the
worker moves on, and the backoff is per series and enforced at dequeue.

Recovery is a re-send: with `OverwriteInstances` enabled the missing instance
is written again, the next stable-series copy finds the series whole, uploads
it, and clears the lost-data record automatically.

### Proposed solution

The reporting is still passive — something has to go and look. Two pieces, in
order:

**1. Push it.** This is the whole fix: re-sending the study repairs it, so
telling someone *which* studies to re-send closes the loop. The plugin should
not decide what a lost series *means* — it has no idea who is meant to hear
about it. When registering the plugin, give it an optional "data loss" 
callback, invoked from the copy thread's abandon guard with a structured
payload (series id, parent study id, instance count, timestamp, reason). The
host application registers it and routes it wherever it needs to go.

**2. Optionally, and later, clean up.** Deleting a lost series/study is *not*
a recovery mechanism — re-upload already is one. It only stops unrepaired
records from accumulating in the index. That is a much weaker justification
for destroying patient records on the strength of a heuristic, so if it is
done at all it must be config-gated and default off, must run only after the
report has been delivered, and must be conservative about false positives —
above all it must never fire for a series that is merely *evicted* (data safe
on S3, local copy reclaimed), which is a normal steady state.

Doing (2) without (1) would delete the only evidence that anything went
wrong, and destroy a study that could have been recovered by re-sending it.

