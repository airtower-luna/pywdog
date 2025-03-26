import os
import pytest
import subprocess
import time
import wdog
from textwrap import dedent


@pytest.fixture(scope='session')
def watchdogd_bin():
    return os.environ.get('TEST_WATCHDOGD', 'watchdogd')


@pytest.fixture(autouse=True)
def watchdogd(tmp_path, watchdogd_bin):
    wdog_config = tmp_path / 'watchdogd.conf'
    wdog_config.write_text(dedent('''\
    supervisor {
        enabled = true
    }
    '''))
    proc = subprocess.Popen([
        watchdogd_bin, '-f', str(wdog_config), '-n', '--test-mode',
        '--loglevel=debug'], stderr=subprocess.PIPE)
    for _ in range(10):
        if wdog.ping():
            break
        time.sleep(.1)
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
