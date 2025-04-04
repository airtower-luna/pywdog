import pytest
import shutil
from pathlib import Path

watchdogd_key = pytest.StashKey[str | None]()


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        '--watchdogd-bin', action='store', type=str, default=None,
        help='watchdogd binary to use in tests')


def pytest_configure(config: pytest.Config):
    w = config.getoption('--watchdogd-bin') or shutil.which('watchdogd')
    config.stash[watchdogd_key] = w


def pytest_report_header(config: pytest.Config, start_path: Path):
    return [
        f'watchdogd: {config.stash[watchdogd_key]}'
    ]


@pytest.fixture(scope='session')
def watchdogd_bin(pytestconfig: pytest.Config) -> str:
    if (w := pytestconfig.stash[watchdogd_key]) is None:
        raise Exception('watchdogd not found')
    return w
