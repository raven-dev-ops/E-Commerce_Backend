import logging
import time
from django.conf import settings
from django.db.backends.signals import connection_created
from prometheus_client import Histogram

logger = logging.getLogger(__name__)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Duration of database queries in seconds",
    ["alias"],
)


def _wrap_execute(connection):
    alias = connection.alias

    def wrapper(execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            duration = time.perf_counter() - start
            DB_QUERY_DURATION.labels(alias=alias).observe(duration)
            threshold = getattr(settings, "DB_SLOW_QUERY_THRESHOLD", 0.5)
            if duration > threshold:
                logger.warning("Slow query (%.3fs): %s", duration, sql)

    connection.execute_wrapper(wrapper)


def connection_created_handler(connection, **kwargs):
    """Attach query execution wrapper to new DB connections."""
    _wrap_execute(connection)


connection_created.connect(connection_created_handler)
