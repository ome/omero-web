#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   Copyright 2008-2020 The Open Microscopy Environment, Glencoe Software, Inc.
   All rights reserved.

   Use is subject to license terms supplied in LICENSE.txt

"""

import os
import sys

from setuptools import setup, find_packages

sys.path.append(".")
from omeroweb.version import omeroweb_version as owv  # noqa
from omeroweb.version import omero_version as opv  # noqa


def read(fname):
    """
    Utility function to read the README file.
    :rtype : String
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="omero-web",
    version=owv,
    description="OMERO.web",
    long_description=read("README.rst"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v2 " "or later (GPLv2+)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],  # Get strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    author="The Open Microscopy Team",
    author_email="ome-devel@lists.openmicroscopy.org.uk",
    url="https://github.com/ome/omero-web/",
    license="GPLv2+",
    packages=find_packages(exclude=("test",)) + ["omero.plugins"],
    python_requires=">=3.8",
    install_requires=[
        # requires Ice (use wheel for faster installs)
        "omero-py>=5.7.0",
        # minimum requirements for `omero web start`
        "concurrent-log-handler>=0.9.20",
        "Django>=4.2.3,<4.3",
        "django-pipeline==2.1.0",
        "django-cors-headers==3.7.0",
        "whitenoise>=5.3.0",
        "gunicorn>=19.3",
        "omero-marshal>=0.7.0",
        "Pillow",
        "pytz",
        "portalocker",
        "packaging",
    ],
    include_package_data=True,
    tests_require=["pytest"],
    extras_require={
        "redis": ["django-redis==5.3.0"],
    },
)
