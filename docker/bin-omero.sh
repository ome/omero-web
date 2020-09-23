#!/bin/sh

export OMERODIR=${OMERODIR:-/opt/omero/web/OMERO.web}
export PATH=/opt/omero/web/venv3/bin:$PATH
exec /opt/omero/web/venv3/bin/omero "$@"
