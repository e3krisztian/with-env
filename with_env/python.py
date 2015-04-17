#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
'''
Run program within a python environment with specified list of packages.

The environment is defined in a requirements.txt
'''

from __future__ import unicode_literals
from __future__ import print_function

from . import VERSION as __version__

import argparse
import argcomplete
from datetime import datetime
import hashlib
import heapq
import os
import sys
import shutil
import subprocess
import tempfile

try:
    # Py3
    from os import getcwdb as os_getcwdb
except:
    # Py2
    from os import getcwd as os_getcwdb

# environment variables
PATH = 'PATH'
VIRTUAL_ENV = 'VIRTUAL_ENV'
XDG_CACHE_HOME = 'XDG_CACHE_HOME'

# cache size
MAX_CACHED_VIRTUALENVS = 10


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
    if os.path.getsize(requirements_txt) == 0:
        return
    cmd = ['pip', 'install', '-r', requirements_txt, '--quiet']
    subprocess.check_call(cmd, stdout=sys.stderr)


def call_program(program, program_args):
    cmd = [program] + program_args
    return subprocess.call(cmd)

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S %f'


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
        write_activate_timestamp(self.virtualenv_dir)
        os.environ[VIRTUAL_ENV] = self.virtualenv_dir
        virtualenv_bin = os.path.join(self.virtualenv_dir, 'bin')
        os.environ[PATH] = virtualenv_bin + os.pathsep + os.environ[PATH]


def activate_timestamp_file(virtualenv_dir):
    return os.path.join(virtualenv_dir, 'activate.ts')


def write_activate_timestamp(virtualenv_dir):
    activate_ts = activate_timestamp_file(virtualenv_dir)
    with open(activate_ts, 'wb') as timestamp:
        timestamp.write(
            datetime.now().strftime(TIMESTAMP_FORMAT).encode('utf-8'))


def read_activate_timestamp(virtualenv_dir):
    activate_ts = activate_timestamp_file(virtualenv_dir)
    with open(activate_ts, 'rb') as ts_file:
        ts_string = ts_file.read().decode('utf-8')
        return datetime.strptime(ts_string, TIMESTAMP_FORMAT)


def remove_old_virtualenvs():
    lru = []
    cache_dir = virtualenv_cache_dir()
    virtualenvs = os.listdir(cache_dir)
    if len(virtualenvs) <= MAX_CACHED_VIRTUALENVS:
        return

    for dir in virtualenvs:
        virtualenv_dir = os.path.join(cache_dir, dir)
        try:
            ts = read_activate_timestamp(virtualenv_dir)
            heapq.heappush(lru, (ts, virtualenv_dir))
        except IOError:
            # not a virtualenv?
            remove_directory(virtualenv_dir)
        if len(lru) > MAX_CACHED_VIRTUALENVS:
            ts, virtualenv_dir = heapq.heappop(lru)
            remove_directory(virtualenv_dir)


def cache_dir():
    if XDG_CACHE_HOME in os.environ:
        return os.environ[XDG_CACHE_HOME]
    return os.path.expanduser('~/.cache')


def virtualenv_cache_dir():
    return os.path.join(cache_dir(), 'python-virtualenvs')


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
            virtualenv_cache_dir(), self.virtualenv_hash)

    def __enter__(self):
        if not os.path.isdir(self.virtualenv_dir):
            self.install()
        else:
            self.activate()
        remove_old_virtualenvs()

    def __exit__(self, *args, **kwargs):
        pass

    @property
    def virtualenv_hash(self):
        sha1 = hashlib.sha1()

        def add_part(bytes):
            sha1.update(str(len(bytes)).encode('utf-8'))
            sha1.update(':'.encode('utf-8'))
            sha1.update(bytes)

        add_part((self.custom_python or '').encode('utf-8'))
        add_part(os_getcwdb())
        with open(self.requirements_txt, 'rb') as f:
            add_part(f.read())
        return sha1.hexdigest()


def virtualenv(args, note):
    custom_python = args.python
    requirements_txt = args.requirements

    if args.no_cache:
        venv = TemporaryVirtualenv(custom_python, requirements_txt, note)
    else:
        venv = CachedVirtualenv(custom_python, requirements_txt, note)

        if args.recreate:
            note('Removing {}', venv.virtualenv_dir)
            remove_directory(venv.virtualenv_dir)

    return venv


def silent_note(*args, **kwargs):
    pass


def verbose_note(msg, *args, **kwargs):
    sys.stderr.write('*** '.encode('utf-8'))
    sys.stderr.write(msg.format(*args, **kwargs).encode('utf-8'))
    sys.stderr.write('\n'.encode('utf-8'))


DESCRIPTION = '''\
Run program within a python environment with specified list of packages.
'''


def make_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    arg = parser.add_argument
    # options
    arg('-p', '--python',
        help='Specify alternative python interpreter')
    arg(
        '-r', '--requirements',
        metavar='REQUIREMENTS.TXT',
        default='requirements.txt',
        help='File to read requirements from (default: %(default)s)'
    ).completer = argcomplete.completers.FilesCompleter
    arg('--recreate',
        action='store_true', default=False,
        help='Delete cached virtualenv and create it again')
    arg('--no-cache',
        action='store_true', default=False,
        help='Ignore cached virtualenv and use a temporary one')
    arg('-v', '--verbose',
        action='store_true', default=False,
        help='''Show what's happening''')
    arg('--version', action='version', version='%(prog)s ' + __version__)
    # mandatory arguments
    arg('program',
        help='Program to execute in the virtualenv, bash is a useful value')
    arg('args', nargs='*',
        help='Parameters to pass to the program')
    return parser


def main():
    parser = make_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    program = args.program
    program_args = args.args
    note = verbose_note if args.verbose else silent_note

    with virtualenv(args, note=note):
        note('Executing {} {}', program, ' '.join(program_args))
        retcode = call_program(program, program_args)
        raise SystemExit(retcode)


if __name__ == '__main__':
    main()
