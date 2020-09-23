#!/bin/bash

set -eu

export PATH="/opt/omero/web/venv3/bin:$PATH"
omero=/opt/omero/web/OMERO.web/bin/omero
cd /opt/omero/web
echo "Starting OMERO.web"
exec $omero web start --foreground
