Tools to execute commands requiring external resources without previous setup.

Provides two commands:

- `with-newdb`, which creates a new, empty postgresql database for the program
- `with-python`, which creates a virtualenv populated with the packages
  specified in the `requirements.txt` parameter


Install with::

	pip install -e git+https://github.com/krisztianfekete/with-env.git#egg=with-env

or

	pip install with-env

from the private repo.
