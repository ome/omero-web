OMERO.web
=========
.. image::  https://github.com/ome/omero-web/workflows/Tox/badge.svg
    :target: https://github.com/ome/omero-web/actions

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. image:: https://badge.fury.io/py/omero-web.svg
    :target: https://badge.fury.io/py/omero-web

Introduction
------------

OMERO.web provides a web based client and plugin infrastructure.

Dependencies
------------

Direct dependencies of OMERO.web are:

- `OMERO.py`_
- `ZeroC IcePy`_
- `Pillow`_
- `NumPy`_
- A WSGI capable web server

Installation
------------

We recommend installing omero-web in a Python virtual environment.
Here we show the install using `Conda`_. For more details and
other options, please see `OMERO.py`_.

    conda create -n myenv -c ome python=3.6 zeroc-ice36-python omero-py
    conda activate myenv
    pip install omero-web

Setting of the environment variable ``OMERODIR`` is required.
``$OMERODIR/var/log/`` directory will contain log files.
``$OMERODIR/etc/grid/config.xml`` is used to store config::

    export OMERODIR=$(pwd)

Usage
-----

For running omero-web in production with nginx, see See: `OMERO.web install`_ documentation.
To run in development mode, see below.

Contributing
------------

See: `OMERO`_ documentation

Developer installation
----------------------

For a development installation we recommend creating a virtual environment as described above.
Then install OMERO.web into your virtual environment as an editable package, so that any edits
to source files will be reflected in your installation.

::

    git clone https://github.com/ome/omero-web
    cd omero-web
    pip install -e .

Note some omero-web tests may not run when this module and/or omero-py are installed in editable mode.

Configuration for developer usage::

    omero config set omero.web.debug True
    omero config set omero.web.application_server development

    # If you want to connect to OMERO.server other than 'localhost'
    omero config append omero.web.server_list '["demo.openmicroscopy.org", 4064, "demo"]'

Then run omero-web in the foreground with::

    omero web start
    ...
    Starting development server at http://127.0.0.1:4080/

Or, run Django directly::

    cd omero-web
    python omeroweb/manage.py runserver 4080
    ...
    Starting development server at http://127.0.0.1:4080/

Running tests
-------------

Unit tests are located under the `test` directory and can be run with pytest.

Integration tests
^^^^^^^^^^^^^^^^^

Integration tests are stored in the main repository (ome/openmicroscopy) and depend on the
OMERO integration testing framework. Reading about `Running and writing tests`_ in the `OMERO`_ documentation
is essential.

Release process
---------------

This repository uses `bump2version <https://pypi.org/project/bump2version/>`_ to manage version numbers.
To tag a release run::

    $ bumpversion release

This will remove the ``.dev0`` suffix from the current version, commit, and tag the release.

To switch back to a development version run::

    $ bumpversion --no-tag patch

NB: this assumes next release will be a ``patch`` (see below).
To complete the release, push the master branch and the release tag to origin::

    $ git push origin master v5.8.0

If any PRs are merged that would require the next release to be a ``major`` or ``minor`` version
(see `semver.org <https://semver.org/>`_) then that PR can include a version bump created via::

    $ bumpversion --no-tag minor|major

If this hasn't been performed prior to release and you wish to specify the next version
number directly when creating the release, this can be achieved with::

    $ bumpversion --new-version 5.9.0 release

omero-web-docker
^^^^^^^^^^^^^^^^

Following ``omero-web`` release, need to update and release ``omero-web-docker``.

License
-------

OMERO.web is released under the AGPL.

Copyright
---------

2009-2020, The Open Microscopy Environment, Glencoe Software, Inc.

.. _OMERO: https://www.openmicroscopy.org/omero
.. _OMERO.web install: https://docs.openmicroscopy.org/latest/omero/sysadmins/unix/install-web/web-deployment.html
.. _OMERO.py: https://pypi.python.org/pypi/omero-py
.. _ZeroC IcePy: https://zeroc.com/
.. _Pillow: https://python-pillow.org/
.. _NumPy: http://matplotlib.org/
.. _Running and writing tests: https://docs.openmicroscopy.org/latest/omero/developers/testing.html
.. _Conda: https://docs.conda.io/en/latest/
