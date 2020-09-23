#!/bin/sh
# Run .omero files from /opt/omero/web/config/
set -eu

omero=/opt/omero/web/OMERO.web/bin/omero

$omero load --glob /opt/omero/web/config/*.omero

OMEROHOST=${OMEROHOST:-}
if [ -n "$OMEROHOST" ]; then
    $omero config set omero.web.server_list "[[\"$OMEROHOST\", 4064, \"omero\"]]"
fi
