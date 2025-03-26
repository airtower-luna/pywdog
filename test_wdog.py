import os
import pytest
import subprocess
import time
import wdog
from pathlib import Path
from textwrap import dedent


@pytest.fixture(scope='session')
def watchdogd_bin():
    return os.environ.get('TEST_WATCHDOGD', 'watchdogd')


@pytest.fixture(scope='session')
def watchdogd_config(tmp_path_factory) -> Path:
    wdog_config = tmp_path_factory.mktemp('watchdogd') / 'watchdogd.conf'
    wdog_config.write_text(dedent('''\
    supervisor {
        enabled = true
    }
    '''))
    return wdog_config


def start_watchdogd(executable: str, config: Path) -> subprocess.Popen:
    proc = subprocess.Popen([
        executable, '-f', str(config), '-n', '--test-mode',
        '--loglevel=debug'])
    for _ in range(10):
        if wdog.ping():
            break
        time.sleep(.1)
    return proc


@pytest.fixture(autouse=True)
def watchdogd(watchdogd_bin, watchdogd_config):
    proc = start_watchdogd(watchdogd_bin, watchdogd_config)
    yield proc
    if proc.poll() is None:
        proc.terminate()
        proc.communicate()


def test_ping():
    assert wdog.ping()


def test_full(watchdogd):
    w = wdog.Wdog('test')
    w.subscribe(2000)
    for _ in range(5):
        time.sleep(.5)
        w.pet()
    w.unsubscribe()


@pytest.mark.parametrize('label', [None, b'test'])
def test_labels(label):
    w = wdog.Wdog(label)
    w.subscribe(2000)
    w.pet()
    w.unsubscribe()


def test_fail(watchdogd):
    w = wdog.Wdog(b'test')
    w.subscribe(1000)
    w.pet()
    watchdogd.communicate(None, timeout=2)


def test_extend():
    w = wdog.Wdog('extend')
    w.subscribe(1000)
    w.extend(2000)
    time.sleep(1.5)
    w.pet()
    w.unsubscribe()


@pytest.mark.parametrize('method', ['pet', 'extend'])
def test_reconnect(
        method, watchdogd_bin: str, watchdogd_config: Path, watchdogd):
    w = wdog.Wdog('extend')
    w.subscribe(1000)
    w.pet()
    watchdogd.terminate()
    watchdogd.communicate()
    proc = start_watchdogd(watchdogd_bin, watchdogd_config)
    try:
        getattr(w, 'pet')()
        w.unsubscribe()
    finally:
        proc.terminate()
        proc.communicate()


def test_reconnect_fail(watchdogd):
    w = wdog.Wdog('extend')
    w.subscribe(1000)
    w.pet()
    watchdogd.terminate()
    watchdogd.communicate()
    with pytest.raises(ConnectionRefusedError):
        w.pet()
