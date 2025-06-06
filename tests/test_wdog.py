import os
import pytest
import subprocess
import time
import wdog
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


@dataclass
class WatchdogPaths:
    bin: str
    config: Path
    dev: Path
    events: Path


@pytest.fixture(scope='session')
def watchdogd_setup(tmp_path_factory, watchdogd_bin: str) -> WatchdogPaths:
    wdog_dir = tmp_path_factory.mktemp('watchdogd')
    wdog_files = WatchdogPaths(
        watchdogd_bin,
        wdog_dir / 'watchdogd.conf',
        wdog_dir / 'dev',
        wdog_dir / 'events.log',
    )

    wdog_files.dev.touch()

    wdog_script = wdog_dir / 'supervisor.sh'
    wdog_script.write_text(dedent(f'''\
    #!/bin/sh
    echo "${{@}}" >>{wdog_files.events!s}
    '''))
    wdog_script.chmod(0o755)
    wdog_files.events.touch()

    wdog_files.config.write_text(dedent(f'''\
    device {wdog_files.dev!s} {{}}
    supervisor {{
        enabled = true
        script = "{wdog_script!s}"
    }}
    '''))
    return wdog_files


def start_watchdogd(setup: WatchdogPaths) -> subprocess.Popen:
    proc = subprocess.Popen([
        setup.bin, '-f', str(setup.config), '-n', '--loglevel=debug'])
    os.truncate(setup.events, 0)
    for _ in range(10):
        if wdog.ping():
            break
        time.sleep(.1)
    return proc


@pytest.fixture(autouse=True)
def watchdogd(watchdogd_setup: WatchdogPaths) \
        -> Iterator[subprocess.Popen]:
    proc = start_watchdogd(watchdogd_setup)
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


def test_full(watchdogd_setup: WatchdogPaths):
    w = wdog.Wdog('test')
    w.subscribe(2.0)
    for _ in range(6):
        time.sleep(.5)
        w.pet()
    w.unsubscribe()
    assert watchdogd_setup.events.stat().st_size == 0


@pytest.mark.parametrize('label', [None, b'test'])
def test_labels(label):
    w = wdog.Wdog(label)
    w.subscribe(2.0)
    w.pet()
    w.unsubscribe()


def test_fail(watchdogd_setup: WatchdogPaths):
    label = 'test'
    w = wdog.Wdog(label)
    w.subscribe(1)
    w.pet()
    time.sleep(1)
    with watchdogd_setup.events.open() as fh:
        for _ in range(20):
            event = fh.readline().strip()
            if event:
                break
            time.sleep(.1)
    print(event)
    fields = event.split(' ', maxsplit=3)
    # fixed value, part of supervisor script API
    assert fields[0] == 'supervisor'
    # reset reason, 5: "PID failed to meet its deadline"
    assert int(fields[1]) == 5
    # PID
    assert int(fields[2]) == os.getpid()
    assert fields[3] == label


def test_set_timeout(watchdogd_setup: WatchdogPaths):
    w = wdog.Wdog('set_timeout')
    w.subscribe(1)
    w.set_timeout(2.5)
    time.sleep(1.8)
    w.pet()
    w.unsubscribe()
    assert watchdogd_setup.events.stat().st_size == 0


@pytest.mark.parametrize('method', ['pet', 'set_timeout'])
def test_reconnect(
        method: str, watchdogd_setup: WatchdogPaths,
        watchdogd: subprocess.Popen):
    w = wdog.Wdog(method)
    w.subscribe(1)
    w.pet()
    watchdogd.terminate()
    watchdogd.communicate()
    proc = start_watchdogd(watchdogd_setup)
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
