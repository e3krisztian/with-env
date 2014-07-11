#!/usr/bin/env python
'''
Run program within a python environment with specified list of packages.

Usage:
    with-req [options] [--] <program> [<args>...]

Options:
    -p <python>, --python <python>
                Specify alternative python interpreter

    -r <requirements.txt>, --requirements <requirements.txt>
                File to read requirements from [default: requirements.txt]

    -v, --version                   Show program version
    -h, --help                      This help
'''

from __future__ import unicode_literals
from __future__ import print_function

from . import VERSION

import os
import shutil
import subprocess
import tempfile
from docopt import docopt


PATH = 'PATH'
VIRTUAL_ENV = 'VIRTUAL_ENV'


def new_temporary_directory(prefix):
    return tempfile.mkdtemp(prefix=prefix)


def remove_directory(directory):
    shutil.rmtree(directory, ignore_errors=True)


def create_virtualenv(custom_python, virtualenv_dir):
    cmd = (
        ['virtualenv', '--quiet']
        + (['-p', custom_python] if custom_python else [])
        + [virtualenv_dir]
    )
    subprocess.check_call(cmd)


def enter_virtualenv(virtualenv_dir):
    os.environ[VIRTUAL_ENV] = virtualenv_dir
    virtualenv_bin = os.path.join(virtualenv_dir, 'bin')
    os.environ[PATH] = virtualenv_bin + os.pathsep + os.environ[PATH]


def install_packages(requirements_txt):
    cmd = ['pip', 'install', '-r', requirements_txt, '--quiet']
    subprocess.check_call(cmd)


def call_program(program, program_args):
    cmd = [program] + program_args
    return subprocess.call(cmd)


def main():
    args = docopt(__doc__, version=VERSION, options_first=True)

    custom_python = args['--python']
    requirements_txt = args['--requirements']
    program = args['<program>']
    program_args = args['<args>']

    virtualenv_dir = new_temporary_directory('pytmpvenv')
    try:
        create_virtualenv(custom_python, virtualenv_dir)
        enter_virtualenv(virtualenv_dir)
        install_packages(requirements_txt)

        retcode = call_program(program, program_args)
        raise SystemExit(retcode)
    finally:
        remove_directory(virtualenv_dir)


if __name__ == '__main__':
    main()
