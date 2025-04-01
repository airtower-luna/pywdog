import nox
from pathlib import Path

wrapper = Path(__file__).parent / 'test-namespace-wrapper.sh'


@nox.session(python=['3.13'])
def test(session):
    """Run tests."""
    session.install('.[tests]')
    session.run(
        'sh', str(wrapper),
        'pytest', '--cov=wdog', '--cov-report=term', '-v',
        env={'COVERAGE_FILE': f'.coverage.{session.python}'}, external=True)
    session.notify('coverage')


@nox.session
def coverage(session):
    """Generate combined coverage report."""
    session.install('coverage')
    session.run('coverage', 'combine')
    session.run('coverage', 'html')
