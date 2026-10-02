# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""Numbering that does not spend the real numbers.

PostgreSQL sequences ignore transactions: a ``nextval`` drawn while trying
something out stays drawn after the rollback, and a flow replayed five times
would eat five order numbers.  So nothing here calls ``nextval``.  The next
number is read without consuming it and then counted on locally.

It doubles as the marker for "a simulation is running in this thread", which
is how module installs are kept out of one.
"""

import threading
from contextlib import contextmanager

_local = threading.local()


@contextmanager
def own_numbering():
    """Hand out numbers locally for the duration of the block."""
    previous = getattr(_local, "counters", None)
    _local.counters = {}
    try:
        yield
    finally:
        _local.counters = previous


def counters():
    """The counters in force here, or None when numbering is for real."""
    return getattr(_local, "counters", None)


def simulating():
    """Whether a simulation is running in this thread."""
    return counters() is not None
