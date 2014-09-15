#!/usr/bin/env python
'''
Run program within a python environment with specified list of packages.

Usage:
    in-virtualenv [options] [--] <program> [<args>...]

Options:
    -p <python>, --python <python>
                    Specify alternative python interpreter

    -r <requirements.txt>, --requirements <requirements.txt>
                    File to read requirements from [default: requirements.txt]

    --recreate      Delete cached virtualenv and create it again
    --no-cache      Ignore cached virtualenv and use a temporary one

    --verbose       Show what's happening
    -v, --version   Show program version
    -h, --help      This help
'''

from __future__ import unicode_literals
from __future__ import print_function

from . import VERSION

import hashlib
import os
import sys
import shutil
import subprocess
import tempfile
from docopt import docopt


# environment variables
PATH = 'PATH'
VIRTUAL_ENV = 'VIRTUAL_ENV'
XDG_CACHE_HOME = 'XDG_CACHE_HOME'


def new_temporary_directory(prefix):
    return tempfile.mkdtemp(prefix=prefix)


def remove_directory(directory):
    shutil.rmtree(directory, ignore_errors=True)


def create_virtualenv(custom_python, virtualenv_dir):
    cmd = (
        ['virtualenv', '--quiet']
        + (['--python', custom_python] if custom_python else [])
        + [virtualenv_dir]
    )
    subprocess.check_call(cmd, stdout=sys.stderr)


def install_packages(requirements_txt):
    cmd = ['pip', 'install', '-r', requirements_txt, '--quiet']
    subprocess.check_call(cmd, stdout=sys.stderr)


def call_program(program, program_args):
    cmd = [program] + program_args
    return subprocess.call(cmd)


class Virtualenv(object):

    def __init__(self, custom_python, requirements_txt, note):
        self.note = note
        self.custom_python = custom_python
        self.requirements_txt = requirements_txt
        self.virtualenv_dir = None

    def install(self):
        self.note('Installing virtualenv {}', self.virtualenv_dir)
        try:
            create_virtualenv(self.custom_python, self.virtualenv_dir)
            self.activate()
            self.note('Installing requirements from {}', self.requirements_txt)
            install_packages(self.requirements_txt)
        except:
            self.note('Error happened, removing {}', self.virtualenv_dir)
            remove_directory(self.virtualenv_dir)
            raise

    def activate(self):
        self.note('Activating virtualenv {}', self.virtualenv_dir)
        os.environ[VIRTUAL_ENV] = self.virtualenv_dir
        virtualenv_bin = os.path.join(self.virtualenv_dir, 'bin')
        os.environ[PATH] = virtualenv_bin + os.pathsep + os.environ[PATH]


class TemporaryVirtualenv(Virtualenv):

    def __enter__(self):
        self.virtualenv_dir = new_temporary_directory('pytmpenv')
        self.note('Created temporary directory {}', self.virtualenv_dir)
        self.install()

    def __exit__(self, *args, **kwargs):
        self.note('Removing temporary directory {}', self.virtualenv_dir)
        remove_directory(self.virtualenv_dir)


class CachedVirtualenv(Virtualenv):

    def __init__(self, *args, **kwargs):
        super(CachedVirtualenv, self).__init__(*args, **kwargs)
        self.virtualenv_dir = os.path.join(
            self.cache_dir,
            'python-virtualenvs',
            self.virtualenv_hash
        )

    def __enter__(self):
        if not os.path.isdir(self.virtualenv_dir):
            self.install()
        else:
            self.activate()

    def __exit__(self, *args, **kwargs):
        pass

    @property
    def virtualenv_hash(self):
        with open(self.requirements_txt, 'rb') as f:
            sha1 = hashlib.sha1((self.custom_python or '').encode('utf-8'))
            sha1.update('\n')
            sha1.update(f.read())
            return sha1.hexdigest()

    @property
    def cache_dir(self):
        if XDG_CACHE_HOME in os.environ:
            return os.environ[XDG_CACHE_HOME]
        return os.path.expanduser('~/.cache')


def virtualenv(args, note):
    custom_python = args['--python']
    requirements_txt = args['--requirements']

    if args['--no-cache']:
        venv = TemporaryVirtualenv(custom_python, requirements_txt, note)
    else:
        venv = CachedVirtualenv(custom_python, requirements_txt, note)

        if args['--recreate']:
            note('Removing {}', venv.virtualenv_dir)
            remove_directory(venv.virtualenv_dir)

    return venv


def silent_note(*args, **kwargs):
    pass


def verbose_note(msg, *args, **kwargs):
    sys.stderr.write('*** '.encode('utf-8'))
    sys.stderr.write(msg.format(*args, **kwargs).encode('utf-8'))
    sys.stderr.write('\n'.encode('utf-8'))


def main():
    args = docopt(__doc__, version=VERSION, options_first=True)

    program = args['<program>']
    program_args = args['<args>']
    note = verbose_note if args['--verbose'] else silent_note

    with virtualenv(args, note=note):
        note('Executing {} {}', program, ' '.join(program_args))
        retcode = call_program(program, program_args)
        raise SystemExit(retcode)


if __name__ == '__main__':
    main()
