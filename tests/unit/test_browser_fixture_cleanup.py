"""The browser fixture closes resources even when setup never reaches yield."""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from tests.browser import test_workbench as workbench


@pytest.mark.parametrize('failure', ['launch', 'context', 'page', 'goto', 'close', None])
def test_connected_fixture_cleans_partial_setup(monkeypatch, failure):
    """Red if fixture cleanup starts only after browser/page creation or skips server exit."""
    events = []

    class Socket:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def bind(self, *_):
            pass

        def getsockname(self):
            return '127.0.0.1', 12345

    runner = SimpleNamespace(started=True, should_exit=False, run=lambda: None)

    class Thread:
        ident = None

        def __init__(self, **_):
            self.alive = False

        def start(self):
            self.alive = True
            self.ident = 1
            events.append('thread-start')

        def join(self, **_):
            self.alive = False
            events.append('thread-join')

        def is_alive(self):
            return self.alive

    def fail(stage):
        if failure == stage:
            raise RuntimeError('injected-' + stage)

    page = SimpleNamespace(on=lambda *_: None, locator=lambda *_: object())
    page.goto = lambda *_: fail('goto')
    context = SimpleNamespace(close=lambda: (events.append('context-close'), fail('close')))
    context.new_page = lambda: (fail('page'), page)[1]
    browser = SimpleNamespace(close=lambda: events.append('browser-close'))
    browser.new_context = lambda **_: (fail('context'), context)[1]

    @contextmanager
    def playwright():
        def launch(**_):
            fail('launch')
            return browser
        yield SimpleNamespace(chromium=SimpleNamespace(launch=launch))

    monkeypatch.setattr(workbench, 'socket', SimpleNamespace(socket=Socket))
    monkeypatch.setattr(workbench, 'threading', SimpleNamespace(Thread=Thread))
    monkeypatch.setattr(workbench, 'uvicorn', SimpleNamespace(
        Config=lambda *_args, **_kwargs: object(), Server=lambda _: runner))
    monkeypatch.setattr(workbench, 'sync_playwright', playwright)
    monkeypatch.setattr(workbench, 'expect', lambda _: SimpleNamespace(to_be_enabled=lambda: None))
    fixture = workbench.connected_browser.__wrapped__(SimpleNamespace(param={}))
    if failure and failure != 'close':
        with pytest.raises(RuntimeError, match='injected-' + failure):
            next(fixture)
    else:
        assert next(fixture)[0] is page
        if failure == 'close':
            with pytest.raises(RuntimeError, match='injected-close'):
                next(fixture)
        else:
            with pytest.raises(StopIteration):
                next(fixture)
    assert 'thread-start' in events
    assert runner.should_exit and 'thread-join' in events
    if failure != 'launch':
        assert 'browser-close' in events
    if failure not in ('launch', 'context'):
        assert 'context-close' in events
