#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   Copyright 2008-2019 The Open Microscopy Environment, Glencoe Software, Inc.
   All rights reserved.

   Use is subject to license terms supplied in LICENSE.txt

"""

import os

from setuptools import setup, find_packages

VERSION = "5.5.1"


def read(fname):
    """
    Utility function to read the README file.
    :rtype : String
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name="omero-web",
      version=VERSION,
      description="OMERO.web",
      long_description=read("README.rst"),
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 '
        'or later (GPLv2+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],  # Get strings from
          # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      author="The Open Microscopy Team",
      author_email="ome-devel@lists.openmicroscopy.org.uk",
      url="https://github.com/ome/omero-web/",
      license='GPLv2+',
      packages=find_packages(exclude=("test",))+["omero.plugins"],
      install_requires=[
          # No Ice included, since a native wheel is preferable
          # Otherwise, minimum requirements for `omero web start`
          'omero-py',
          'Django>=1.8,<1.9'
          'django-pipeline==1.3.20',
          'gunicorn>=19.3',
          'omero-marshal>=0.6.1',
      ],
      include_package_data=True,
      tests_require=['pytest<3'],
      )
