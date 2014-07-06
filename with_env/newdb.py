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

VERSION = '0.1.0'

from datetime import datetime
import os
import subprocess
from docopt import docopt


def generate_database_name(prefix):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    pid = os.getpid()
    database_name = '{}_{}_{}'.format(prefix, timestamp, pid)
    return database_name


def call_program(program, program_args):
    cmd = [program] + program_args
    subprocess.check_call(cmd)


def create_database(database_name):
    call_program('createdb', ['--encoding=UTF8', database_name])


def drop_database(database_name):
    return call_program('dropdb', [database_name])


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

        call_program(program, program_args)
    finally:
        if not keep_database:
            drop_database(database_name)


if __name__ == '__main__':
    main()
