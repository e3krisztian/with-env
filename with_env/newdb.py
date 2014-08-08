#!/usr/bin/env python
'''
Run program with a new empty postgresql database as default database.

Default database is the one `psql` connects to without any parameter.

Usage:
    with-newdb [options] [--] <program> [<args>...]

Options:
    -p <prefix>, --prefix <prefix>  New database name prefix [default: tmp]
    -k, --keep                      Keep the database after for debug purposes
    -v, --version                   Show program version
    -h, --help                      This help
'''

from __future__ import unicode_literals
from __future__ import print_function

from . import VERSION

from datetime import datetime
import os
import sys
import subprocess
from docopt import docopt


def generate_database_name(prefix):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    pid = os.getpid()
    database_name = '{}_{}_{}'.format(prefix, timestamp, pid)
    return database_name


def call_program(program, program_args):
    cmd = [program] + program_args
    return subprocess.call(cmd)


def create_database(database_name):
    cmd = ['createdb', '--encoding=UTF8', database_name]
    subprocess.check_call(cmd, stdout=sys.stderr)


def drop_database(database_name):
    cmd = ['dropdb', database_name]
    subprocess.check_call(cmd, stdout=sys.stderr)


def make_database_default(database_name):
    os.environ['PGDATABASE'] = database_name


def main():
    args = docopt(__doc__, version=VERSION, options_first=True)

    keep_database = args['--keep']
    prefix = args['--prefix']
    program = args['<program>']
    program_args = args['<args>']

    database_name = generate_database_name(prefix)
    create_database(database_name)
    try:
        make_database_default(database_name)

        retcode = call_program(program, program_args)
        raise SystemExit(retcode)
    finally:
        if not keep_database:
            drop_database(database_name)


if __name__ == '__main__':
    main()
