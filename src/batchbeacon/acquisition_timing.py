"""Bounded, content-free request timing. Observations confer no authority.

Each transition closes the previous span using one process monotonic clock.
The fixed stage vocabulary bounds memory; heartbeats never create transitions.
The HTTP worker owns this object through completion, including disconnects.
"""

import asyncio
import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock
from time import monotonic
from uuid import uuid4

STAGES = ('ownership', 'preparation', 'model_setup', 'count', 'admission', 'provider',
          'response_storage', 'model_cleanup', 'accounting', 'validation', 'persistence',
          'saved_status', 'response')
PUBLIC_STAGES = {'ownership': 'preparing', 'preparation': 'preparing',
    'model_setup': 'preparing', 'count': 'preparing', 'admission': 'preparing',
    'provider': 'model', 'response_storage': 'saving', 'model_cleanup': 'saving',
    'accounting': 'saving', 'validation': 'saving', 'persistence': 'saving',
    'saved_status': 'saving', 'response': 'saving'}
_current = ContextVar('acquisition_timing', default=None)
# Uvicorn configures its own loggers, not the application root. This dedicated
# content-free sink must work under the exact container command without DEBUG.
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.propagate = False
if not _logger.handlers:
    _logger.addHandler(logging.StreamHandler())


class AcquisitionTiming:
    def __init__(self, policy_hash):
        self.policy_hash = policy_hash
        self.correlation = uuid4().hex
        self._lock = Lock()
        self._started = self._since = monotonic()
        self._stage = None
        self._spans = []
        self._public = []
        self._finished = False
        self._binding = {}
        self._loop = asyncio.get_running_loop()
        self.changed = asyncio.Event()

    def begin(self, stage):
        if stage not in STAGES:
            return
        with self._lock:
            # Each stage is visited at most once; telemetry cannot grow with input.
            if self._finished or stage == self._stage or any(s['stage'] == stage
                                                           for s in self._spans):
                return
            now = monotonic()
            if self._stage is not None:
                self._spans.append({'stage': self._stage, 'seconds': now - self._since})
            self._stage, self._since = stage, now
            public = PUBLIC_STAGES[stage]
            rank = ('preparing', 'model', 'saving').index(public)
            if not self._public or rank > ('preparing', 'model', 'saving').index(self._public[-1]):
                self._public.append(public)
                self._loop.call_soon_threadsafe(self.changed.set)

    def bind(self, run_id, request_hash, configuration_hash):
        with self._lock:
            self._binding = {'run_id': run_id, 'request_hash': request_hash,
                             'configuration_hash': configuration_hash}

    def progress(self):
        with self._lock:
            return tuple(self._public)

    def finish(self, outcome):
        with self._lock:
            if self._finished:
                return
            self._finished = True
            now = monotonic()
            if self._stage:
                self._spans.append({'stage': self._stage, 'seconds': now - self._since})
            record = {'event': 'acquisition_timing_v1', 'correlation': self.correlation,
                'policy_hash': self.policy_hash, 'outcome': outcome,
                'seconds': now - self._started, 'spans': self._spans, 'binding': self._binding}
        # Content-free application log; existing private Cloud Logging access/retention applies.
        # A failing handler must never alter acquisition/accounting behavior.
        try:
            _logger.info(json.dumps(record, separators=(',', ':')))
        except Exception:
            pass
        return record


@contextmanager
def observe(timing):
    token = _current.set(timing)
    try:
        yield
    finally:
        _current.reset(token)


def stage(name):
    timing = _current.get()
    if timing is not None:
        timing.begin(name)


def bind(run_id, request_hash, configuration_hash):
    timing = _current.get()
    if timing is not None:
        timing.bind(run_id, request_hash, configuration_hash)
