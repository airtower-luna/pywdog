import os
import nox
from pathlib import Path

wrapper = Path(__file__).parent / 'test-namespace-wrapper.sh'
build_dir = Path(__file__).parent / 'noxbuild'


@nox.session(python=['3.13'])
def test(session):
    """Run tests."""
    session.install('.[tests]', f'--config-settings=build-dir={build_dir!s}')
    testenv = {
        'COVERAGE_FILE': f'.coverage.{session.python}'
    }
    # If watchdogd was built as subproject, use it unless there's an
    # explicit override.
    watchdogd_internal = build_dir \
        / 'subprojects/watchdogd/dist/usr/local/sbin/watchdogd'
    if watchdogd_internal.is_file() and 'TEST_WATCHDOGD' not in os.environ:
        testenv['TEST_WATCHDOGD'] = str(watchdogd_internal)
    session.run(
        'sh', str(wrapper),
        'pytest', '--cov=wdog', '--cov-report=term', '-v',
        env=testenv, external=True)
    session.notify('coverage')


@nox.session
def coverage(session):
    """Generate combined coverage report."""
    session.install('coverage')
    session.run('coverage', 'combine')
    session.run('coverage', 'html')
