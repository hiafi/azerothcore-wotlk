"""
The SQL replay cache for the data tests: `under_replay_cache` runs a loader under generate.py's sqlcorpus cache
(var/dbc-tools-cache, keyed by the replay code's version), so the live-state loaders (trainer index, spell / creature
table index, live DSL data, existing DBC rows) read checkpoints instead of replaying the whole SQL migration history.
A class data test that loads them without it spends minutes per load.

Only for loaders over the real source tree and migrations: while a corpus is active it memoises what it reads, so a
test that writes its own SQL into a temp directory and replays it must stay outside.
"""

from __future__ import annotations

import functools
from contextlib import contextmanager

from lib import sqlcorpus


@contextmanager
def replay_cache():
    """Activates the cache for the block, unless one is already active (the outer block owns it then)."""
    if sqlcorpus.active() is not None:
        yield
        return
    import generate  # noqa: PLC0415 - heavy; imports this package

    sqlcorpus.activate(generate.CACHE_DIR, generate.cache_code_version())
    try:
        yield
    finally:
        sqlcorpus.deactivate()


def under_replay_cache(fn):
    """Decorator form of `replay_cache`."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with replay_cache():
            return fn(*args, **kwargs)
    return wrapper
