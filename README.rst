OMERO.web
=========

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

See: `OMERO`_ documentation

Usage
-----

See: `OMERO`_ documentation

Contributing
------------

See: `OMERO`_ documentation

Developer installation
----------------------

OMERO.web depends on OMERO.py. If you want a developer installation of OMERO.py, replace ``pip install omero-py``
with instructions at https://github.com/ome/omero-py.

For a development installation we recommend creating a virtualenv with the following setup (example assumes ``python3.6`` but you can create and activate the virtualenv using any compatible Python):

::

    python3.6 -mvenv venv
    . venv/bin/activate
    pip install zeroc-ice==3.6.5
    pip install omero-py          # OR dev install (see above)
    git clone https://github.com/ome/omero-web
    cd omero-web
    pip install -e .

This will install OMERO.web into your virtualenv as an editable package, so any edits to source files should be reflected in your installation.
Note that if you add or remove files you must rerun the last step.

Running tests
-------------

Unit tests are located under the `test` directory and can be run with pytest.

Integration tests
^^^^^^^^^^^^^^^^^

Integration tests are stored in the main repository (ome/openmicroscopy) and depend on the
OMERO integration testing framework. Reading about `Running and writing tests`_ in the `OMERO`_ documentation
is essential.

License
-------

OMERO.web is released under the AGPL.

Copyright
---------

2009-2019, The Open Microscopy Environment, Glencoe Software, Inc.

.. _OMERO: https://www.openmicroscopy.org/omero
.. _OMERO.py: https://pypi.python.org/pypi/omero-py
.. _ZeroC IcePy: https://zeroc.com/
.. _Pillow: https://python-pillow.org/
.. _NumPy: http://matplotlib.org/
.. _Running and writing tests: https://docs.openmicroscopy.org/latest/omero/developers/testing.html
