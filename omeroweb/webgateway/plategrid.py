# -*- coding: utf-8 -*-

# Copyright (C) 2015 Glencoe Software, Inc.
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.txt

"""
   Module to encapsulate operations concerned with displaying the contents of a
   plate as a grid.
"""

import logging

import omero.sys
from omero.rtypes import rint, rlong


logger = logging.getLogger(__name__)


class PlateGrid(object):
    """
    A PlateGrid object encapsulates a PlateI reference and provides a number of
    methods useful for displaying the contents of the plate as a grid.
    """

    def __init__(self, conn, pid, fid, thumbprefix="", plate_layout=None, acqid=None):
        """
        Constructor

        param:  plate_layout is "expand" to expand plate to multiple of 8 x 12
                or "shrink" to ignore all wells before the first row/column

                fid: the field index relative to the lowest "absolute field index"
                for that well. When filtering the image samples with an
                acquisition ID (acqid), the lowest field index may be
                different for each well.
                In the range [0, max_sample_per_well]
                (or [0, max_sample_per_well_per_acquisition] with an acqid)

                acqid: the acquisition ID to filter the WellSamples.
        """
        self.plate = conn.getObject("plate", int(pid))
        self._conn = conn
        self.field = fid
        self.acquisition = acqid
        self._thumbprefix = thumbprefix
        self._metadata = None
        self.plate_layout = plate_layout

    @property
    def metadata(self):
        if self._metadata is None:
            q = self._conn.getQueryService()
            params = omero.sys.ParametersI()
            params.addId(self.plate.id)
            params.add("wsidx", rint(self.field))
            query = (
                "select well.row, well.column, img.id, img.name, "
                "author.firstName||' '||author.lastName, "
                "well.id, img.acquisitionDate, "
                "img.details.creationEvent.time, "
                "img.description "
                "from Well well "
                "join well.wellSamples ws "
                "join ws.image img "
                "join img.details.owner author "
                "where well.plate.id = :id "
            )
            if self.acquisition is not None:
                # Offseting field index per well for the plateacquisition
                query += (
                    "and ws.plateAcquisition.id = :acqid "
                    "and index(ws) - ("
                    "    SELECT MIN(index(ws_inner)) "
                    "    FROM Well well_inner "
                    "    JOIN well_inner.wellSamples ws_inner "
                    "    WHERE ws_inner.plateAcquisition.id = :acqid "
                    "    AND well_inner.id = well.id "
                    ") = :wsidx "
                )
                params.add("acqid", rlong(self.acquisition))
            else:
                query += "and index(ws) = :wsidx "

            results = q.projection(query, params, self._conn.SERVICE_OPTS)
            min_row = 0
            min_col = 0
            if self.plate_layout == "expand":
                self.plate.setGridSizeConstraints(8, 12)
            elif self.plate_layout == "shrink":
                # need to know min row/col, regardless of field index
                params = omero.sys.ParametersI()
                params.addId(self.plate.id)
                query = (
                    "select min(well.row), min(well.column) "
                    "from Well well "
                    "where well.plate.id = :id"
                )
                min_vals = q.projection(query, params, self._conn.SERVICE_OPTS)
                min_row = min_vals[0][0].val
                min_col = min_vals[0][1].val
            collabels = self.plate.getColumnLabels()[min_col:]
            rowlabels = self.plate.getRowLabels()[min_row:]
            grid = [[None] * len(collabels) for _ in range(len(rowlabels))]

            for res in results:
                (
                    row,
                    col,
                    img_id,
                    img_name,
                    author,
                    well_id,
                    acq_date,
                    create_date,
                    description,
                ) = res

                if acq_date is not None and acq_date.val > 0:
                    date = acq_date.val // 1000
                else:
                    date = create_date.val // 1000
                description = (description and description.val) or ""

                wellmeta = {
                    "type": "Image",
                    "id": img_id.val,
                    "name": img_name.val,
                    "description": description,
                    "author": author.val,
                    "date": date,
                    "wellId": well_id.val,
                    "field": self.field,
                }

                if callable(self._thumbprefix):
                    wellmeta["thumb_url"] = self._thumbprefix(str(img_id.val))
                else:
                    wellmeta["thumb_url"] = self._thumbprefix + str(img_id.val)

                grid[row.val - min_row][col.val - min_col] = wellmeta

            # find dimensions of first image, to help in layout
            img_sizes = []
            if len(results) > 0:
                image_id = results[0][2].val
                params = omero.sys.ParametersI()
                params.addId(image_id)
                query = (
                    "select pixels.sizeX, pixels.sizeY "
                    "from Pixels pixels "
                    "where pixels.image.id = :id"
                )
                sizes = q.projection(query, params, self._conn.SERVICE_OPTS)
                if len(sizes) > 0:
                    size_x = sizes[0][0].val
                    size_y = sizes[0][1].val
                    img_sizes.append({"x": size_x, "y": size_y, "image_id": image_id})

            self._metadata = {
                "grid": grid,
                "collabels": collabels,
                "rowlabels": rowlabels,
                "image_sizes": img_sizes,
            }
        return self._metadata
