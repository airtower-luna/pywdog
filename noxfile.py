import nox
from pathlib import Path

wrapper = Path(__file__).parent / 'test-namespace-wrapper.sh'


@nox.session(python=['3.13'])
def test(session):
    """Run tests."""
    session.install('.[tests]')
    session.run('sh', str(wrapper), 'pytest', '-v', external=True)
