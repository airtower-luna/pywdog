import os
import pytest
import re
import subprocess
import time
import wdog
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


@dataclass
class WatchdogFiles:
    config: Path
    state: Path


@pytest.fixture(scope='session')
def watchdogd_setup(tmp_path_factory) -> WatchdogFiles:
    wdog_dir = tmp_path_factory.mktemp('watchdogd')
    wdog_files = WatchdogFiles(
        wdog_dir / 'watchdogd.conf',
        wdog_dir / 'watchdogd.state',
    )
    wdog_dev = wdog_dir / 'dev'
    wdog_dev.touch()
    wdog_files.config.write_text(dedent(f'''\
    device {wdog_dev!s} {{
        timeout    = 15
        interval   = 7
        safe-exit  = true
    }}
    supervisor {{
        enabled = true
    }}
    reset-reason {{
        enabled = true
        file = "{wdog_files.state!s}"
    }}
    '''))
    return wdog_files


def start_watchdogd(executable: str, config: Path) -> subprocess.Popen:
    proc = subprocess.Popen([
        executable, '-f', str(config), '-n', '--loglevel=debug'])
    for _ in range(10):
        if wdog.ping():
            break
        time.sleep(.1)
    return proc


def parse_state(statefile: Path) -> dict[str, str]:
    state: dict[str, str] = dict()
    with statefile.open('r') as fh:
        for line in fh:
            m = re.match(r'^(.*\w)\s+:\s+(\S.*)$', line)
            assert m is not None
            state[m.group(1)] = m.group(2)
    return state


@pytest.fixture(autouse=True)
def watchdogd(watchdogd_bin: str, watchdogd_setup: WatchdogFiles) \
        -> Iterator[subprocess.Popen]:
    proc = start_watchdogd(watchdogd_bin, watchdogd_setup.config)
    yield proc
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()


def test_ping():
    assert wdog.ping()


def test_full(watchdogd):
    w = wdog.Wdog('test')
    w.subscribe(2.0)
    for _ in range(5):
        time.sleep(.5)
        w.pet()
    w.unsubscribe()


@pytest.mark.parametrize('label', [None, b'test'])
def test_labels(label):
    w = wdog.Wdog(label)
    w.subscribe(2.0)
    w.pet()
    w.unsubscribe()


def test_fail(watchdogd_setup: WatchdogFiles, watchdogd: subprocess.Popen):
    label = 'test'
    w = wdog.Wdog(label)
    w.subscribe(1)
    subscribed = time.time()
    w.pet()
    for _ in range(20):
        if watchdogd_setup.state.is_file() \
           and watchdogd_setup.state.stat().st_mtime > subscribed:
            break
        time.sleep(.1)
    state = parse_state(watchdogd_setup.state)
    print(state)
    assert int(state['PID']) == os.getpid()
    assert state['Label'] == label
    assert 'Failed to meet deadline' in state['Reset reason']


def test_set_timeout():
    w = wdog.Wdog('set_timeout')
    w.subscribe(1)
    w.set_timeout(2.0)
    time.sleep(1.5)
    w.pet()
    w.unsubscribe()


@pytest.mark.parametrize('method', ['pet', 'set_timeout'])
def test_reconnect(
        method: str, watchdogd_bin: str, watchdogd_setup: WatchdogFiles,
        watchdogd: subprocess.Popen):
    w = wdog.Wdog(method)
    w.subscribe(1)
    w.pet()
    watchdogd.terminate()
    watchdogd.communicate()
    proc = start_watchdogd(watchdogd_bin, watchdogd_setup.config)
    try:
        if method == 'extend':
            w.set_timeout(1.5)
        else:
            w.pet()
        w.unsubscribe()
    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()


def test_reconnect_fail(watchdogd: subprocess.Popen):
    w = wdog.Wdog('reconnect_fail')
    w.subscribe(1)
    w.pet()
    watchdogd.terminate()
    watchdogd.communicate()
    with pytest.raises((ConnectionRefusedError, BlockingIOError)):
        w.pet()


def test_too_short():
    w = wdog.Wdog('too_short')
    with pytest.raises(ValueError):
        w.subscribe(.2)


@pytest.mark.parametrize('method', ['pet', 'set_timeout', 'unsubscribe'])
def test_invalid_state(method: str):
    w = wdog.Wdog('invalid_state')
    with pytest.raises(wdog.WdogStateException, match=r'not subscribed'):
        if method == 'set_timeout':
            getattr(w, method)(1.0)
        else:
            getattr(w, method)()


def test_double_subscribe():
    w = wdog.Wdog('invalid_state')
    w.subscribe(2.0)
    with pytest.raises(wdog.WdogStateException, match=r'already subscribed'):
        w.subscribe(2.0)
    w.pet()
    w.unsubscribe()
