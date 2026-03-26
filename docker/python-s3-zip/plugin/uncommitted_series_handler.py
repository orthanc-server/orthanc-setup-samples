import orthanc
from s3zip_logging import get_logger

logger = get_logger(__name__)

UNCOMMITTED_SERIES_KVS = "uncommitted-series"


class UncommittedSeriesHandler:

    def __init__(self):
        pass


    def on_new_series(self, series_id: str):
        logger.debug(f"Adding new uncommitted series {series_id}")
        orthanc.StoreKeyValue(UNCOMMITTED_SERIES_KVS, series_id, "0")  # '0' because we can not store empty/null values


    def on_committed_series(self, series_id: str):
        logger.debug(f"Committing series {series_id}")
        orthanc.DeleteKeyValue(UNCOMMITTED_SERIES_KVS, series_id)


    def on_orthanc_started(self):
        it = orthanc.CreateKeysValuesIterator(UNCOMMITTED_SERIES_KVS)
        uncommitted_series_ids = []
        while it.Next():
            uncommitted_series_ids.append(it.GetKey())

        if len(uncommitted_series_ids) == 0:
            logger.info(f"no uncommitted series found at startup")
            return

        logger.info(f"{len(uncommitted_series_ids)} uncommitted series found at startup, removing them ...")

        for series_id in uncommitted_series_ids:
            try:
                logger.info(f"Deleting uncommitted series {series_id}")
                orthanc.RestApiDelete(f'/series/{series_id}')
            except:
                pass
            orthanc.DeleteKeyValue(UNCOMMITTED_SERIES_KVS, series_id)
