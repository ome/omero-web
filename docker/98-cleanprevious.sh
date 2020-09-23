#!/bin/bash
# This image isn't cleanly shutdown by docker stop
# https://github.com/openmicroscopy/omero-web-docker/issues/1
# This is a workaround until we figure out the root cause
set -eu

rm -f /opt/omero/web/OMERO.web/var/django.pid
