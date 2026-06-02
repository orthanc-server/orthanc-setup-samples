import time
import orthanc
from s3zip_logging import get_logger

logger = get_logger(__name__)

UNCOMMITTED_SERIES_KVS = "uncommitted-series"


class UncommittedSeriesHandler:

    def __init__(self):
        pass


    def on_new_series(self, series_id: str):
        # The value is the epoch-millisecond timestamp at which we first
        # learned about the series. The housekeeper uses it to decide when
        # an entry has lingered long enough to count as "stuck". Legacy
        # entries (value "0") are still accepted and treated as very old
        # by the housekeeper's parser.
        logger.debug(f"Adding new uncommitted series {series_id}")
        try:
            orthanc.StoreKeyValue(UNCOMMITTED_SERIES_KVS, series_id, str(int(time.time() * 1000)))
        except Exception:
            # KVS write failures are not fatal: STABLE_SERIES will still
            # fire and schedule the copy. The housekeeper safety net is
            # what we lose. Log and move on so we don't break the
            # Orthanc-side change-event dispatch.
            logger.exception("Failed to record uncommitted series", series_id=series_id)


    def on_committed_series(self, series_id: str):
        logger.debug(f"Committing series {series_id}")
        try:
            orthanc.DeleteKeyValue(UNCOMMITTED_SERIES_KVS, series_id)
        except Exception:
            # Same reasoning as on_new_series: do not let a transient KVS
            # error break the copy worker. The housekeeper will reconcile.
            logger.exception("Failed to clear uncommitted-series KVS entry", series_id=series_id)
