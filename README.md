Tools to execute commands requiring external resources without previous setup.

Provides two commands::

- `with-newdb`, which creates a new, empty postgresql database for the program
- `with-req`, which runs its program inside a virtualenv populated with the packages specified in `requirements.txt`

Both commands can be arbitrarily nested.

Example::

    with-newdb with-req -r converter/requirements.txt convert.sh

Install with::

    pip install -e git+https://github.com/krisztianfekete/with-env.git#egg=with-env

or

    pip install with-env

from the private repo.
