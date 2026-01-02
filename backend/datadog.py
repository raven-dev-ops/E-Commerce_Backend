import os
import sys
from importlib import util

"""Optional DataDog APM integration."""

_testing = bool(
    os.getenv("CI")
    or os.getenv("TESTING")
    or os.getenv("PYTEST_CURRENT_TEST")
    or "test" in sys.argv
)

# Only patch if ddtrace is installed, tracing is enabled, and we're not testing
if (
    not _testing
    and util.find_spec("ddtrace")
    and os.getenv("DD_TRACE_ENABLED", "true").lower() in {"true", "1"}
):
    from ddtrace import patch_all  # type: ignore

    patch_all()
