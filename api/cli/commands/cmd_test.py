import os
import subprocess
import click

@click.command()
@click.argument('path', default=os.path.join('api', 'tests'))
def cli(path):
    """
    Run a test coverage report.

    :param path: Test coverage path
    :return: Subprocess call result
    """
    cmd = 'py.test {0}'.format(path)
    return subprocess.call(cmd, shell=True)