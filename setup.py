#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   Copyright 2008-2016 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import glob
import sys
import os

from setuptools import setup, find_packages

setup(name="omero-web",
      version="5.5.dev1",
      description="OmeroWeb",
      long_description="""\
OmeroWeb is the container of the web clients for OMERO."
""",
      author="The Open Microscopy Team",
      author_email="ome-devel@lists.openmicroscopy.org.uk",
      url="https://github.com/openmicroscopy/openmicroscopy/",
      download_url="https://github.com/openmicroscopy/openmicroscopy/",
      packages=find_packages(exclude=("test",))+["omero.plugins"],
      include_package_data=True,
      tests_require=['pytest<3'],
      )
