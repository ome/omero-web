#!/bin/sh
# Run .omero files from /opt/omero/web/config/
set -eu

/opt/omero/web/OMERO.web/bin/omero load --glob /opt/omero/web/config/*.omero
