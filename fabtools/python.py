"""
Python environments and packages
================================

This module includes tools for using `virtual environments`_
and installing packages using `pip`_.

.. _virtual environments: http://www.virtualenv.org/
.. _pip: http://www.pip-installer.org/

"""
from __future__ import with_statement

from contextlib import contextmanager
from distutils.version import StrictVersion as V
from pipes import quote
import os
import posixpath

from fabric.api import cd, hide, prefix, run, settings, sudo
from fabric.utils import puts

from fabtools.files import is_file
from fabtools.utils import abspath, run_as_root


def is_pip_installed(version=None, pip_cmd='pip'):
    """
    Check if `pip`_ is installed.

    .. _pip: http://www.pip-installer.org/
    """
    with settings(hide('running', 'warnings', 'stderr', 'stdout'), warn_only=True):
        res = run('%(pip_cmd)s --version 2>/dev/null' % locals())
        if res.failed:
            return False
        if version is None:
            return res.succeeded
        else:
            installed = res.split(' ')[1]
            if V(installed) < V(version):
                puts("pip %s found (version >= %s required)" % (installed, version))
                return False
            else:
                return True


def install_pip(python_cmd='python', use_sudo=True):
    """
    Install the latest version of `pip`_, using the given Python
    interpreter.

    ::

        import fabtools

        if not fabtools.python.is_pip_installed():
            fabtools.python.install_pip()

    .. note::
        pip is automatically installed inside a virtualenv, so there
        is no need to install it yourself in this case.

    .. _pip: http://www.pip-installer.org/
    """

    with cd('/tmp'):

        run('curl --silent -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py')

        command = '%(python_cmd)s get-pip.py' % locals()
        if use_sudo:
            run_as_root(command, pty=False)
        else:
            run(command, pty=False)

        run('rm -f get-pip.py')

def is_installed(package, pip_cmd='pip'):
    """
    Check if a Python package is installed (using pip).

    Package names are case insensitive.

    Example::

        from fabtools.python import virtualenv
        import fabtools

        with virtualenv('/path/to/venv'):
            fabtools.python.install('Flask')
            assert fabtools.python.is_installed('flask')

    .. _pip: http://www.pip-installer.org/
    """
    with settings(hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True):
        res = run('%(pip_cmd)s freeze' % locals())
    packages = [line.split('==')[0].lower() for line in res.splitlines()]
    return (package.lower() in packages)


def install(packages, upgrade=False, use_mirrors=False, use_sudo=False,
            user=None, download_cache=None, quiet=False, pip_cmd='pip'):
    """
    Install Python package(s) using `pip`_.

    Package names are case insensitive.

    Examples::

        import fabtools

        # Install a single package
        fabtools.python.install('package', use_sudo=True)

        # Install a list of packages
        fabtools.python.install(['pkg1', 'pkg2'], use_sudo=True)

    .. _pip: http://www.pip-installer.org/
    """
    if not isinstance(packages, basestring):
        packages = ' '.join(packages)

    options = []
    if use_mirrors:
        options.append('--use-mirrors')
    if upgrade:
        options.append('--upgrade')
    if download_cache:
        options.append('--download-cache="%s"' % download_cache)
    if quiet:
        options.append('--quiet')
    options = ' '.join(options)

    command = '%(pip_cmd)s install %(options)s %(packages)s' % locals()

    if use_sudo:
        sudo(command, user=user, pty=False)
    else:
        run(command, pty=False)


def install_requirements(filename, upgrade=False, use_mirrors=False,
                         use_sudo=False, user=None, download_cache=None,
                         quiet=False, pip_cmd='pip'):
    """
    Install Python packages from a pip `requirements file`_.

    ::

        import fabtools

        fabtools.python.install_requirements('project/requirements.txt')

    .. _requirements file: http://www.pip-installer.org/en/latest/requirements.html
    """
    options = []
    if use_mirrors:
        options.append('--use-mirrors')
    if upgrade:
        options.append('--upgrade')
    if download_cache:
        options.append('--download-cache="%s"' % download_cache)
    if quiet:
        options.append('--quiet')
    options = ' '.join(options)

    command = '%(pip_cmd)s install %(options)s -r %(filename)s' % locals()

    if use_sudo:
        sudo(command, user=user, pty=False)
    else:
        run(command, pty=False)


def create_virtualenv(directory, system_site_packages=False, venv_python=None,
               use_sudo=False, user=None, clear=False, prompt=None,
               virtualenv_cmd='virtualenv'):
    """
    Create a Python `virtual environment`_.

    ::

        import fabtools

        fabtools.python.create_virtualenv('/path/to/venv')

    .. _virtual environment: http://www.virtualenv.org/
    """
    options = ['--quiet']
    if system_site_packages:
        options.append('--system-site-packages')
    if venv_python:
        options.append('--python=%s' % quote(venv_python))
    if clear:
        options.append('--clear')
    if prompt:
        options.append('--prompt=%s' % quote(prompt))
    options = ' '.join(options)

    directory = quote(directory)

    command = '%(virtualenv_cmd)s %(options)s %(directory)s' % locals()
    if use_sudo:
        sudo(command, user=user)
    else:
        run(command)


def virtualenv_exists(directory):
    """
    Check if a Python `virtual environment`_ exists.

    .. _virtual environment: http://www.virtualenv.org/
    """
    return is_file(posixpath.join(directory, 'bin', 'python'))


@contextmanager
def virtualenv(directory, local=False):
    """
    Context manager to activate an existing Python `virtual environment`_.

    ::

        from fabric.api import run
        from fabtools.python import virtualenv

        with virtualenv('/path/to/virtualenv'):
            run('python -V')

    .. _virtual environment: http://www.virtualenv.org/
    """

    path_mod = os.path if local else posixpath

    # Build absolute path to the virtualenv activation script
    venv_path = abspath(directory)
    activate_path = path_mod.join(venv_path, 'bin', 'activate')

    # Source the activation script
    with prefix('. %s' % quote(activate_path)):
        yield
