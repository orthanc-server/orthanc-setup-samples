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

