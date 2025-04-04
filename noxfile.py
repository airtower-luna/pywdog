import nox
import shutil
from pathlib import Path

repo = Path(__file__).parent
wrapper = repo / 'test-namespace-wrapper.sh'
build_dir = repo / 'noxbuild'
cov_dir = repo / 'htmlcov'


@nox.session(python=['3.13'])
def test(session):
    """Run tests."""
    # The build-dir option is for meson-python, it creates a stable
    # build dir so we can use watchdogd if built as subproject.
    session.install('.[tests]', f'--config-settings=build-dir={build_dir!s}')

    # If watchdogd was built as subproject, use it.
    watchdogd_internal = build_dir \
        / 'subprojects/watchdogd/dist/usr/local/sbin/watchdogd'
    if watchdogd_internal.is_file():
        watchdogd_opt = (f'--watchdogd-bin={watchdogd_internal!s}',)
    else:
        watchdogd_opt = ()

    session.run(
        'sh', str(wrapper),
        'pytest', '--cov=wdog', '--cov-report=term', '-v',
        *watchdogd_opt,
        env={'COVERAGE_FILE': f'.coverage.{session.python}'},
        external=True)
    session.notify('coverage')


@nox.session
def coverage(session):
    """Generate combined coverage report."""
    session.install('coverage')
    session.run('coverage', 'combine')
    session.run('coverage', 'html', '-d', str(cov_dir))


@nox.session(default=False, python=False)
def clean(session):
    for d in (build_dir, cov_dir, repo / '.coverage'):
        try:
            if d.is_dir():
                shutil.rmtree(d)
            else:
                d.unlink()
        except FileNotFoundError:
            pass
