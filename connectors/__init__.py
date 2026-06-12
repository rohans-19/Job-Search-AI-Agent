"""
connectors/__init__.py
----------------------
Makes `connectors` a Python package and exposes the public surface area
so callers can simply do:

    from connectors import get_all_jobs
"""

from .aggregator import get_all_jobs

__all__ = ["get_all_jobs"]
