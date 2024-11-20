#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# webgateway/views.py - django application view handling functions
#
# Copyright (c) 2007-2020 Glencoe Software, Inc. All rights reserved.
#
# This software is distributed under the terms described by the LICENCE file
# you can find at the root of the distribution bundle, which states you are
# free to use it only for non commercial purposes.
# If the file is missing please request a copy by contacting
# jason@glencoesoftware.com.
#
# Author: Carlos Neves <carlos(at)glencoesoftware.com>

import re
import json
import base64
import warnings
from functools import wraps
import omero
import omero.clients

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseServerError,
    JsonResponse,
    HttpResponseForbidden,
)
from django.http import (
    HttpResponseRedirect,
    HttpResponseNotAllowed,
    Http404,
    StreamingHttpResponse,
    HttpResponseNotFound,
)

from django.core.cache import cache
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from wsgiref.util import FileWrapper
from omero.rtypes import rlong, unwrap
from omero.constants.namespaces import NSBULKANNOTATIONS
from .util import points_string_to_XY_list, xy_list_to_bbox
from .plategrid import PlateGrid
from omeroweb.version import omeroweb_buildyear as build_year
from .marshal import imageMarshal, shapeMarshal, rgb_int2rgba
from django.templatetags.static import static
from django.views.generic import View
from django.shortcuts import render
from omeroweb.webadmin.forms import LoginForm
from omeroweb.decorators import get_client_ip, is_public_user
from omeroweb.webadmin.webadmin_utils import upgradeCheck

try:
    from hashlib import md5
except Exception:
    from md5 import md5

from io import BytesIO
import tempfile

from omero import ApiUsageException
from omero.util.decorators import timeit, TimeIt
from omeroweb.httprsp import HttpJavascriptResponse, HttpJavascriptResponseServerError
from omeroweb.connector import Connector, Server

import glob


# from models import StoredConnection

from omeroweb.webgateway.webgateway_tempfile import webgateway_tempfile

import logging
import os
import traceback
import time
import zipfile
import shutil

from omeroweb.decorators import login_required, ConnCleaningHttpResponse
from omeroweb.webgateway.util import zip_archived_files, LUTS_IN_PNG
from omeroweb.webgateway.util import get_longs, getIntOrDefault

from PIL import Image, ImageDraw
import numpy


logger = logging.getLogger(__name__)


def index(request):
    """/webgateway/ index placeholder"""
    return HttpResponse("Welcome to webgateway")


def _safestr(s):
    return str(s).encode("utf-8")


# Regular expression that represents the characters in ASCII that are
# allowed in a valid JavaScript variable name.  Function names adhere to
# the same rules.
# See:
#   https://stackoverflow.com/questions/1661197/what-characters-are-valid-for-javascript-variable-names
VALID_JS_VARIABLE = re.compile(r"^[a-zA-Z_$][0-9a-zA-Z_$]*$")


class UserProxy(object):
    """
    Represents the current user of the connection, with methods delegating to
    the connection itself.
    """

    def __init__(self, blitzcon):
        """
        Initialises the User proxy with the L{omero.gateway.BlitzGateway}
        connection

        @param blitzcon:    connection
        @type blitzcon:     L{omero.gateway.BlitzGateway}
        """

        self._blitzcon = blitzcon
        self.loggedIn = False

    def logIn(self):
        """Sets the loggedIn Flag to True"""

        self.loggedIn = True

    def isAdmin(self):
        """
        True if the current user is an admin

        @return:    True if the current user is an admin
        @rtype:     Boolean
        """

        return self._blitzcon.isAdmin()

    def canBeAdmin(self):
        """
        True if the current user can be admin

        @return:    True if the current user can be admin
        @rtype:     Boolean
        """

        return self._blitzcon.canBeAdmin()

    def getId(self):
        """
        Returns the ID of the current user

        @return:    User ID
        @rtype:     Long
        """

        return self._blitzcon.getUserId()

    def getName(self):
        """
        Returns the Name of the current user

        @return:    User Name
        @rtype:     String
        """

        return self._blitzcon.getUser().omeName

    def getFirstName(self):
        """
        Returns the first name of the current user

        @return:    First Name
        @rtype:     String
        """

        return self._blitzcon.getUser().firstName or self.getName()


#    def getPreferences (self):
#        return self._blitzcon._user.getPreferences()
#
#    def getUserObj (self):
#        return self._blitzcon._user
#
# class SessionCB (object):
#    def _log (self, what, c):
#        logger.debug('CONN:%s %s:%d:%s' % (what, c._user, os.getpid(),
#                                           c._sessionUuid))
#
#    def create (self, c):
#        self._log('create',c)
#
#    def join (self, c):
#        self._log('join',c)
#
#    def close (self, c):
#        self._log('close',c)
# _session_cb = SessionCB()


def validate_rdef_query(func):
    @wraps(func)
    def wrapper_validate(request, *args, **kwargs):
        r = None
        try:
            r = request.GET
        except Exception:
            return HttpResponseServerError("Endpoint improperly configured")

        if "c" not in r:
            return HttpResponseBadRequest(
                "Rendering settings must specify channels as c"
            )
        channels, windows, colors = _split_channel_info(r["c"])
        # Need the same number of channels, windows, and colors
        for i in range(0, len(channels)):
            window = windows[i]
            # Unspecified windows and colors are returned as None
            # Validation requires windows to be specified
            if window[0] is None or window[1] is None:
                return HttpResponseBadRequest("Must specify window for each channel")
            if colors[i] is None:
                return HttpResponseBadRequest("Must specify color for each channel")
        if "m" not in r or r["m"] not in ["g", "c"]:
            return HttpResponseBadRequest(
                'Query parameter "m" must be present with value either "g" or "c"'
            )
        # TODO: What to do about z, t, and p?
        if "maps" in r:
            map_json = r["maps"]
            try:
                # If coming from request string, need to load -> json
                if isinstance(map_json, str):
                    map_json = json.loads(map_json)
            except Exception:
                logger.warn("Failed to parse maps JSON")
                return HttpResponseBadRequest("Failed to parse maps JSON")
            rchannels = r["c"].split(",")
            if len(map_json) != len(rchannels):
                return HttpResponseBadRequest(
                    'Number of "maps" must match number of channels'
                )
        return func(request, *args, **kwargs)

    return wrapper_validate


def _split_channel_info(rchannels):
    """
    Splits the request query channel information for images into a sequence of
    channels, window ranges and channel colors.

    @param rchannels:   The request string with channel info. E.g
                        1|100:505$0000FF,-2,3|620:3879$FF0000
    @type rchannels:    String
    @return:            E.g. [1, -2, 3] [[100.0, 505.0], (None, None), [620.0,
                        3879.0]] [u'0000FF', None, u'FF0000']
    @rtype:             tuple of 3 lists
    """

    channels = []
    windows = []
    colors = []
    for chan in rchannels.split(","):
        # chan  1|12:1386r$0000FF
        chan = chan.split("|", 1)
        # chan ['1', '12:1386r$0000FF']
        t = chan[0].strip()
        # t = '1'
        color = None
        # Not normally used...
        if t.find("$") >= 0:
            t, color = t.split("$")
        try:
            channels.append(int(t))
            ch_window = (None, None)
            if len(chan) > 1:
                t = chan[1].strip()
                # t = '12:1386r$0000FF'
                if t.find("$") >= 0:
                    t, color = t.split("$", 1)
                    # color = '0000FF'
                    # t = 12:1386
                t = t.split(":")
                if len(t) == 2:
                    try:
                        ch_window = [float(x) for x in t]
                    except ValueError:
                        pass
            windows.append(ch_window)
            colors.append(color)
        except ValueError:
            pass
    logger.debug(str(channels) + "," + str(windows) + "," + str(colors))
    return channels, windows, colors


def getImgDetailsFromReq(request, as_string=False):
    """
    Break the GET information from the request object into details on how
    to render the image.
    The following keys are recognized:
    z - Z axis position
    t - T axis position
    q - Quality set (0,0..1,0)
    m - Model (g for greyscale, c for color)
    p - Projection (see blitz_gateway.ImageWrapper.PROJECTIONS for keys)
    x - X position (for now based on top/left offset on the browser window)
    y - Y position (same as above)
    c - a comma separated list of channels to be rendered (start index 1)
      - format for each entry [-]ID[|wndst:wndend][#HEXCOLOR][,...]
    zm - the zoom setting (as a percentual value)

    @param request:     http request with keys above
    @param as_string:   If True, return a string representation of the
                        rendering details
    @return:            A dict or String representation of rendering details
                        above.
    @rtype:             Dict or String
    """

    r = request.GET
    rv = {}
    for k in ("z", "t", "q", "m", "zm", "x", "y", "p"):
        if k in r:
            rv[k] = r[k]
    if "c" in r:
        rv["c"] = []
        ci = _split_channel_info(r["c"])
        logger.debug(ci)
        for i in range(len(ci[0])):
            # a = abs channel, i = channel, s = window start, e = window end,
            # c = color
            rv["c"].append(
                {
                    "a": abs(ci[0][i]),
                    "i": ci[0][i],
                    "s": ci[1][i][0],
                    "e": ci[1][i][1],
                    "c": ci[2][i],
                }
            )
    if as_string:
        return "&".join(["%s=%s" % (x[0], x[1]) for x in rv.items()])
    return rv


@login_required()
def render_birds_eye_view(request, iid, size=None, conn=None, **kwargs):
    """
    Returns an HttpResponse wrapped jpeg with the rendered bird's eye view
    for image 'iid'. We now use a thumbnail for performance. #10626

    @param request:     http request
    @param iid:         Image ID
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @param size:        Maximum size of the longest side of the resulting
                        bird's eye view.
    @return:            http response containing jpeg
    """
    return render_thumbnail(request, iid, w=size, **kwargs)


def _render_thumbnail(request, iid, w=None, h=None, conn=None, _defcb=None, **kwargs):
    """
    Returns a jpeg with the rendered thumbnail for image 'iid'

    @param request:     http request
    @param iid:         Image ID
    @param w:           Thumbnail max width. 96 by default
    @param h:           Thumbnail max height
    @return:            http response containing jpeg
    """
    server_settings = request.session.get("server_settings", {}).get("browser", {})
    defaultSize = server_settings.get("thumb_default_size", 96)

    direct = True
    if w is None:
        size = (defaultSize,)
    else:
        if h is None:
            size = (int(w),)
        else:
            size = (int(w), int(h))
    if size == (defaultSize,):
        direct = False
    z = getIntOrDefault(request, "z", None)
    t = getIntOrDefault(request, "t", None)
    rdefId = getIntOrDefault(request, "rdefId", None)
    img = conn.getObject("Image", iid)
    if img is None:
        logger.debug("(b)Image %s not found..." % (str(iid)))
        if _defcb:
            jpeg_data = _defcb(size=size)
        else:
            raise Http404("Failed to render thumbnail")
    else:
        jpeg_data = img.getThumbnail(size=size, direct=direct, rdefId=rdefId, z=z, t=t)
        if jpeg_data is None:
            logger.debug("(c)Image %s not found..." % (str(iid)))
            if _defcb:
                jpeg_data = _defcb(size=size)
            else:
                raise Http404("Failed to render thumbnail")
    return jpeg_data


@login_required()
def render_thumbnail(request, iid, w=None, h=None, conn=None, _defcb=None, **kwargs):
    """
    Returns an HttpResponse wrapped jpeg with the rendered thumbnail for image
    'iid'

    @param request:     http request
    @param iid:         Image ID
    @param w:           Thumbnail max width. 96 by default
    @param h:           Thumbnail max height
    @return:            http response containing jpeg
    """
    jpeg_data = _render_thumbnail(
        request=request, iid=iid, w=w, h=h, conn=conn, _defcb=_defcb, **kwargs
    )
    rsp = HttpResponse(jpeg_data, content_type="image/jpeg")
    return rsp


@login_required()
def render_roi_thumbnail(request, roiId, w=None, h=None, conn=None, **kwargs):
    """
    For the given ROI, choose the shape to render (first time-point, mid
    z-section) then render a region around that shape, scale to width and
    height (or default size) and draw the shape on to the region
    """
    server_id = request.session["connector"]["server_id"]

    # need to find the z indices of the first shape in T
    result = conn.getRoiService().findByRoi(int(roiId), None, conn.SERVICE_OPTS)
    if result is None or result.rois is None or len(result.rois) == 0:
        raise Http404

    for roi in result.rois:
        imageId = roi.image.id.val
        shapes = roi.copyShapes()
    shapes = [s for s in shapes if s is not None]

    if len(shapes) == 0:
        raise Http404("No Shapes found for ROI %s" % roiId)

    pi = _get_prepared_image(request, imageId, server_id=server_id, conn=conn)
    if pi is None:
        raise Http404
    image, compress_quality = pi

    shape = None
    # if only single shape, use it...
    if len(shapes) == 1:
        shape = shapes[0]
    else:
        default_t = image.getDefaultT()
        default_z = image.getDefaultZ()
        # find shapes on default Z/T plane
        def_shapes = [
            s
            for s in shapes
            if unwrap(s.getTheT()) is None or unwrap(s.getTheT()) == default_t
        ]
        if len(def_shapes) == 1:
            shape = def_shapes[0]
        else:
            def_shapes = [
                s
                for s in def_shapes
                if unwrap(s.getTheZ()) is None or unwrap(s.getTheZ()) == default_z
            ]
            if len(def_shapes) > 0:
                shape = def_shapes[0]
        # otherwise pick first shape
        if shape is None and len(shapes) > 0:
            shape = shapes[0]

    return get_shape_thumbnail(request, conn, image, shape, compress_quality)


@login_required()
def render_shape_thumbnail(request, shapeId, w=None, h=None, conn=None, **kwargs):
    """
    For the given Shape, redner a region around that shape, scale to width and
    height (or default size) and draw the shape on to the region.
    """
    server_id = request.session["connector"]["server_id"]

    # need to find the z indices of the first shape in T
    params = omero.sys.Parameters()
    params.map = {"id": rlong(shapeId)}
    shape = conn.getQueryService().findByQuery(
        "select s from Shape s join fetch s.roi where s.id = :id",
        params,
        conn.SERVICE_OPTS,
    )

    if shape is None:
        raise Http404

    imageId = shape.roi.image.id.val

    pi = _get_prepared_image(request, imageId, server_id=server_id, conn=conn)
    if pi is None:
        raise Http404
    image, compress_quality = pi

    return get_shape_thumbnail(request, conn, image, shape, compress_quality)


def get_shape_thumbnail(request, conn, image, s, compress_quality):
    """
    Render a region around the specified Shape, scale to width and height (or
    default size) and draw the shape on to the region. Returns jpeg data.

    @param image:   ImageWrapper
    @param s:       omero.model.Shape
    """

    MAX_WIDTH = 250
    color = request.GET.get("color", "fff")
    colours = {
        "f00": (255, 0, 0),
        "0f0": (0, 255, 0),
        "00f": (0, 0, 255),
        "ff0": (255, 255, 0),
        "fff": (255, 255, 255),
        "000": (0, 0, 0),
    }
    lineColour = colours["f00"]
    if color in colours:
        lineColour = colours[color]
    # used for padding if we go outside the image area
    bg_color = (221, 221, 221)

    bBox = None  # bounding box: (x, y, w, h)
    shape = {}
    theT = unwrap(s.getTheT())
    theT = theT if theT is not None else image.getDefaultT()
    theZ = unwrap(s.getTheZ())
    theZ = theZ if theZ is not None else image.getDefaultZ()
    if isinstance(s, omero.model.RectangleI):
        shape["type"] = "Rectangle"
        shape["x"] = s.getX().getValue()
        shape["y"] = s.getY().getValue()
        shape["width"] = s.getWidth().getValue()
        shape["height"] = s.getHeight().getValue()
        bBox = (shape["x"], shape["y"], shape["width"], shape["height"])
    elif isinstance(s, omero.model.MaskI):
        shape["type"] = "Mask"
        shape["x"] = s.getX().getValue()
        shape["y"] = s.getY().getValue()
        shape["width"] = s.getWidth().getValue()
        shape["height"] = s.getHeight().getValue()
        bBox = (shape["x"], shape["y"], shape["width"], shape["height"])
        # TODO: support for mask
    elif isinstance(s, omero.model.EllipseI):
        shape["type"] = "Ellipse"
        shape["x"] = int(s.getX().getValue())
        shape["y"] = int(s.getY().getValue())
        shape["radiusX"] = int(s.getRadiusX().getValue())
        shape["radiusY"] = int(s.getRadiusY().getValue())
        bBox = (
            shape["x"] - shape["radiusX"],
            shape["y"] - shape["radiusY"],
            2 * shape["radiusX"],
            2 * shape["radiusY"],
        )
    elif isinstance(s, omero.model.PolylineI):
        shape["type"] = "PolyLine"
        shape["xyList"] = points_string_to_XY_list(s.getPoints().getValue())
        bBox = xy_list_to_bbox(shape["xyList"])
    elif isinstance(s, omero.model.LineI):
        shape["type"] = "Line"
        shape["x1"] = int(s.getX1().getValue())
        shape["x2"] = int(s.getX2().getValue())
        shape["y1"] = int(s.getY1().getValue())
        shape["y2"] = int(s.getY2().getValue())
        x = min(shape["x1"], shape["x2"])
        y = min(shape["y1"], shape["y2"])
        bBox = (
            x,
            y,
            max(shape["x1"], shape["x2"]) - x,
            max(shape["y1"], shape["y2"]) - y,
        )
    elif isinstance(s, omero.model.PointI):
        shape["type"] = "Point"
        shape["x"] = s.getX().getValue()
        shape["y"] = s.getY().getValue()
        bBox = (shape["x"] - 50, shape["y"] - 50, 100, 100)
    elif isinstance(s, omero.model.PolygonI):
        shape["type"] = "Polygon"
        shape["xyList"] = points_string_to_XY_list(s.getPoints().getValue())
        bBox = xy_list_to_bbox(shape["xyList"])
    elif isinstance(s, omero.model.LabelI):
        shape["type"] = "Label"
        shape["x"] = s.getX().getValue()
        shape["y"] = s.getY().getValue()
        bBox = (shape["x"] - 50, shape["y"] - 50, 100, 100)
    else:
        logger.debug("Shape type not supported: %s" % str(type(s)))

    # we want to render a region larger than the bounding box
    x, y, w, h = bBox
    # make the aspect ratio (w/h) = 3/2
    requiredWidth = max(w, h * 3 // 2)
    requiredHeight = requiredWidth * 2 // 3
    # make the rendered region 1.5 times larger than the bounding box
    newW = int(requiredWidth * 1.5)
    newH = int(requiredHeight * 1.5)
    # Don't want the region to be smaller than the thumbnail dimensions
    if newW < MAX_WIDTH:
        newW = MAX_WIDTH
        newH = newW * 2 // 3
    # Don't want the region to be bigger than a 'Big Image'!

    def getConfigValue(key):
        try:
            return conn.getConfigService().getConfigValue(key)
        except Exception:
            logger.warn(
                "webgateway: get_shape_thumbnail() could not get"
                " Config-Value for %s" % key
            )
            pass

    max_plane_width = getConfigValue("omero.pixeldata.max_plane_width")
    max_plane_height = getConfigValue("omero.pixeldata.max_plane_height")
    if (
        max_plane_width is None
        or max_plane_height is None
        or (newW > int(max_plane_width))
        or (newH > int(max_plane_height))
    ):
        # generate dummy image to return
        dummy = Image.new("RGB", (MAX_WIDTH, MAX_WIDTH * 2 // 3), bg_color)
        draw = ImageDraw.Draw(dummy)
        draw.text((10, 30), "Shape too large to \ngenerate thumbnail", fill=(255, 0, 0))
        rv = BytesIO()
        dummy.save(rv, "jpeg", quality=90)
        return HttpResponse(rv.getvalue(), content_type="image/jpeg")

    xOffset = (newW - w) // 2
    yOffset = (newH - h) // 2
    newX = int(x - xOffset)
    newY = int(y - yOffset)

    # Need to check if any part of our region is outside the image. (assume
    # that SOME of the region is within the image!)
    sizeX = image.getSizeX()
    sizeY = image.getSizeY()
    left_xs, right_xs, top_xs, bottom_xs = 0, 0, 0, 0
    if newX < 0:
        newW = newW + newX
        left_xs = abs(newX)
        newX = 0
    if newY < 0:
        newH = newH + newY
        top_xs = abs(newY)
        newY = 0
    if newW + newX > sizeX:
        right_xs = (newW + newX) - sizeX
        newW = newW - right_xs
    if newH + newY > sizeY:
        bottom_xs = (newH + newY) - sizeY
        newH = newH - bottom_xs

    # now we should be getting the correct region
    jpeg_data = image.renderJpegRegion(
        theZ, theT, newX, newY, newW, newH, level=None, compression=compress_quality
    )
    img = Image.open(BytesIO(jpeg_data))

    # add back on the xs we were forced to trim
    if left_xs != 0 or right_xs != 0 or top_xs != 0 or bottom_xs != 0:
        jpg_w, jpg_h = img.size
        xs_w = jpg_w + right_xs + left_xs
        xs_h = jpg_h + bottom_xs + top_xs
        xs_image = Image.new("RGB", (xs_w, xs_h), bg_color)
        xs_image.paste(img, (left_xs, top_xs))
        img = xs_image

    # we have our full-sized region. Need to resize to thumbnail.
    current_w, current_h = img.size
    factor = float(MAX_WIDTH) / current_w
    resizeH = int(current_h * factor)
    img = img.resize((MAX_WIDTH, resizeH))

    draw = ImageDraw.Draw(img)
    if shape["type"] == "Rectangle":
        rectX = int(xOffset * factor)
        rectY = int(yOffset * factor)
        rectW = int((w + xOffset) * factor)
        rectH = int((h + yOffset) * factor)
        draw.rectangle((rectX, rectY, rectW, rectH), outline=lineColour)
        # hack to get line width of 2
        draw.rectangle((rectX - 1, rectY - 1, rectW + 1, rectH + 1), outline=lineColour)
    elif shape["type"] == "Line":
        lineX1 = (shape["x1"] - newX + left_xs) * factor
        lineX2 = (shape["x2"] - newX + left_xs) * factor
        lineY1 = (shape["y1"] - newY + top_xs) * factor
        lineY2 = (shape["y2"] - newY + top_xs) * factor
        draw.line((lineX1, lineY1, lineX2, lineY2), fill=lineColour, width=2)
    elif shape["type"] == "Ellipse":
        rectX = int(xOffset * factor)
        rectY = int(yOffset * factor)
        rectW = int((w + xOffset) * factor)
        rectH = int((h + yOffset) * factor)
        draw.ellipse((rectX, rectY, rectW, rectH), outline=lineColour)
        # hack to get line width of 2
        draw.ellipse((rectX - 1, rectY - 1, rectW + 1, rectH + 1), outline=lineColour)
    elif shape["type"] == "Point":
        point_radius = 2
        rectX = (MAX_WIDTH // 2) - point_radius
        rectY = int(resizeH // 2) - point_radius
        rectW = rectX + (point_radius * 2)
        rectH = rectY + (point_radius * 2)
        draw.ellipse((rectX, rectY, rectW, rectH), outline=lineColour)
        # hack to get line width of 2
        draw.ellipse((rectX - 1, rectY - 1, rectW + 1, rectH + 1), outline=lineColour)
    elif "xyList" in shape:
        # resizedXY = [(int(x*factor), int(y*factor))
        #              for (x,y) in shape['xyList']]
        def resizeXY(xy):
            x, y = xy
            return (
                int((x - newX + left_xs) * factor),
                int((y - newY + top_xs) * factor),
            )

        resizedXY = [resizeXY(xy) for xy in shape["xyList"]]
        # doesn't support 'width' of line
        # draw.polygon(resizedXY, outline=lineColour)
        x2 = y2 = None
        for line in range(1, len(resizedXY)):
            x1, y1 = resizedXY[line - 1]
            x2, y2 = resizedXY[line]
            draw.line((x1, y1, x2, y2), fill=lineColour, width=2)
        start_x, start_y = resizedXY[0]
        if shape["type"] != "PolyLine":
            # Seems possible to have Polygon with only 1 point!
            if x2 is None:
                x2 = start_x + 1  # This will create a visible dot
            if y2 is None:
                y2 = start_y + 1
            draw.line((x2, y2, start_x, start_y), fill=lineColour, width=2)

    rv = BytesIO()
    compression = 0.9
    try:
        img.save(rv, "jpeg", quality=int(compression * 100))
        jpeg = rv.getvalue()
    finally:
        rv.close()
    return HttpResponse(jpeg, content_type="image/jpeg")


@login_required()
def render_shape_mask(request, shapeId, conn=None, **kwargs):
    """Returns mask as a png (supports transparency)"""

    params = omero.sys.Parameters()
    params.map = {"id": rlong(shapeId)}
    shape = conn.getQueryService().findByQuery(
        "select s from Shape s where s.id = :id", params, conn.SERVICE_OPTS
    )
    if shape is None:
        raise Http404("Shape ID: %s not found" % shapeId)
    width = int(shape.getWidth().getValue())
    height = int(shape.getHeight().getValue())
    color = unwrap(shape.getFillColor())
    fill = (255, 255, 0, 255)
    if color is not None:
        color = rgb_int2rgba(color)
        fill = (color[0], color[1], color[2], int(color[3] * 255))
    mask_packed = shape.getBytes()
    # convert bytearray into something we can use
    intarray = numpy.fromstring(mask_packed, dtype=numpy.uint8)
    binarray = numpy.unpackbits(intarray)

    # Couldn't get the 'proper' way of doing this to work,
    # TODO: look at this again later. Faster than simple way below:
    # E.g. takes ~2 seconds for 1984 x 1984 mask
    # pixels = ""
    # steps = len(binarray) / 8
    # for i in range(steps):
    #     b = binarray[i*8: (i+1)*8]
    #     pixels += struct.pack("8B", b[0], b[1], b[2], b[3], b[4],
    #                           b[5], b[6], b[7])
    # for b in binarray:
    #     pixels += struct.pack("1B", b)
    # im = Image.frombytes("1", size=(width, height), data=pixels)

    # Simple approach - Just set each pixel in turn
    # E.g. takes ~12 seconds for 1984 x 1984 mask with most pixels '1'
    # Or ~5 seconds for same size mask with most pixels "0"
    img = Image.new("RGBA", size=(width, height), color=(0, 0, 0, 0))
    x = 0
    y = 0
    for pix in binarray:
        if pix == 1:
            img.putpixel((x, y), fill)
        x += 1
        if x > width - 1:
            x = 0
            y += 1
    rv = BytesIO()
    # return a png (supports transparency)
    img.save(rv, "png", quality=int(100))
    png = rv.getvalue()
    return HttpResponse(png, content_type="image/png")


def _get_signature_from_request(request):
    """
    returns a string that identifies this image, along with the settings
    passed on the request.
    Useful for using as img identifier key, for prepared image.

    @param request: http request
    @return:        String
    """

    r = request.GET
    rv = r.get("m", "_") + r.get("p", "_") + r.get("c", "_") + r.get("q", "_")
    return rv


def _get_inverted_enabled(request, sizeC):
    """
    Parses 'maps' query string from request for 'inverted' and 'reverse'

    @param request: http request
    @return:        List of boolean representing whether the
                    corresponding channel is inverted
    """

    inversions = None
    if "maps" in request:
        map_json = request["maps"]
        inversions = []
        try:
            # If coming from request string, need to load -> json
            if isinstance(map_json, str):
                map_json = json.loads(map_json)
            for codomain_map in map_json:
                enabled = False
                # 'reverse' is now deprecated (5.4.0). Check for 'inverted'
                #  first. inverted is True if 'inverted' OR 'reverse' is enabled
                m = codomain_map.get("inverted")
                if m is None:
                    m = codomain_map.get("reverse")
                # If None, no change to saved status
                if m is not None:
                    enabled = m.get("enabled") in (True, "true")
                inversions.append(enabled)
            while len(inversions) < sizeC:
                inversions.append(None)
        except Exception:
            logger.debug("Invalid json for query ?maps=%s" % map_json)
            inversions = None
    return inversions


def _get_prepared_image(
    request, iid, server_id=None, conn=None, saveDefs=False, retry=True
):
    """
    Fetches the Image object for image 'iid' and prepares it according to the
    request query, setting the channels, rendering model and projection
    arguments. The compression level is parsed and returned too.
    For parameters in request, see L{getImgDetailsFromReq}

    @param request:     http request
    @param iid:         Image ID
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @param saveDefs:    Try to save the rendering settings, default z and t.
    @param retry:       Try an extra attempt at this method
    @return:            Tuple (L{omero.gateway.ImageWrapper} image, quality)
    """
    r = request.GET
    logger.debug(
        "Preparing Image:%r saveDefs=%r "
        "retry=%r request=%r conn=%s" % (iid, saveDefs, retry, r, str(conn))
    )
    img = conn.getObject("Image", iid)
    if img is None:
        return

    if "c" in r:
        logger.debug("c=" + r["c"])
        requestedChannels, windows, colors = _split_channel_info(r["c"])
        invert_flags = None
        if "maps" in r:
            invert_flags = _get_inverted_enabled(r, img.getSizeC())
            try:
                # quantization maps (just applied, not saved at the moment)
                # Need to pad the list of quant maps to have one entry per channel
                totalChannels = img.getSizeC()
                channelIndices = [abs(int(ch)) - 1 for ch in requestedChannels]
                qm = [m.get("quantization") for m in json.loads(r["maps"])]
                allMaps = [None] * totalChannels
                for i in range(0, len(channelIndices)):
                    if i < len(qm):
                        allMaps[channelIndices[i]] = qm[i]
                img.setQuantizationMaps(allMaps)
            except Exception:
                logger.info("Failed to set quantization maps")
        allChannels = range(1, img.getSizeC() + 1)
        # If saving, apply to all channels
        if saveDefs and not img.setActiveChannels(
            allChannels, windows, colors, invert_flags
        ):
            logger.debug("Something bad happened while setting the active channels...")
        # Save the active/inactive state of the channels
        if not img.setActiveChannels(requestedChannels, windows, colors, invert_flags):
            logger.debug("Something bad happened while setting the active channels...")

    if r.get("m", None) == "g":
        img.setGreyscaleRenderingModel()
    elif r.get("m", None) == "c":
        img.setColorRenderingModel()
    # projection  'intmax' OR 'intmax|5:25'
    p = r.get("p", None)
    pStart, pEnd = None, None
    if p is not None and len(p.split("|")) > 1:
        p, startEnd = p.split("|", 1)
        try:
            pStart, pEnd = [int(s) for s in startEnd.split(":")]
        except ValueError:
            pass
    img.setProjection(p)
    img.setProjectionRange(pStart, pEnd)
    img.setInvertedAxis(bool(r.get("ia", "0") == "1"))
    compress_quality = r.get("q", None)
    if saveDefs:
        "z" in r and img.setDefaultZ(int(r["z"]) - 1)
        "t" in r and img.setDefaultT(int(r["t"]) - 1)
        img.saveDefaults()
    return (img, compress_quality)


@login_required()
def render_image_region(request, iid, z, t, conn=None, **kwargs):
    """
    Returns a jpeg of the OMERO image, rendering only a region specified in
    query string as region=x,y,width,height. E.g. region=0,512,256,256
    Rendering settings can be specified in the request parameters.

    @param request:     http request
    @param iid:         image ID
    @param z:           Z index
    @param t:           T index
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @return:            http response wrapping jpeg
    """
    server_id = request.session["connector"]["server_id"]

    # if the region=x,y,w,h is not parsed correctly to give 4 ints then we
    # simply provide whole image plane.
    # alternatively, could return a 404?
    # if h == None:
    #    return render_image(request, iid, z, t, server_id=None, _conn=None,
    #                        **kwargs)
    pi = _get_prepared_image(request, iid, server_id=server_id, conn=conn)

    if pi is None:
        raise Http404
    img, compress_quality = pi

    tile = request.GET.get("tile", None)
    region = request.GET.get("region", None)
    level = None

    if tile:
        try:
            img._prepareRenderingEngine()
            w, h = img._re.getTileSize()
            levels = img._re.getResolutionLevels() - 1

            zxyt = tile.split(",")
            # if tile size is given respect it
            if len(zxyt) > 4:
                tile_size = [int(zxyt[3]), int(zxyt[4])]
                tile_defaults = [w, h]
                max_tile_length = 1024
                try:
                    max_tile_length = int(
                        conn.getConfigService().getConfigValue(
                            "omero.pixeldata.max_tile_length"
                        )
                    )
                except Exception:
                    pass
                for i, tile_length in enumerate(tile_size):
                    # use default tile size if <= 0
                    if tile_length <= 0:
                        tile_size[i] = tile_defaults[i]
                    # allow no bigger than max_tile_length
                    if tile_length > max_tile_length:
                        tile_size[i] = max_tile_length
                w, h = tile_size
            v = int(zxyt[0])
            if v < 0:
                msg = "Invalid resolution level %s < 0" % v
                logger.debug(msg, exc_info=True)
                return HttpResponseBadRequest(msg)

            if levels == 0:  # non pyramid file
                if v > 0:
                    msg = "Invalid resolution level %s, non pyramid file" % v
                    logger.debug(msg, exc_info=True)
                    return HttpResponseBadRequest(msg)
                else:
                    level = None
            else:
                level = levels - v
                if level < 0:
                    msg = (
                        "Invalid resolution level, \
                    %s > number of available levels %s "
                        % (v, levels)
                    )
                    logger.debug(msg, exc_info=True)
                    return HttpResponseBadRequest(msg)
            x = int(zxyt[1]) * w
            y = int(zxyt[2]) * h
        except Exception:
            msg = "malformed tile argument, tile=%s" % tile
            logger.debug(msg, exc_info=True)
            return HttpResponseBadRequest(msg)
    elif region:
        try:
            xywh = region.split(",")

            x = int(xywh[0])
            y = int(xywh[1])
            w = int(xywh[2])
            h = int(xywh[3])
        except Exception:
            msg = "malformed region argument, region=%s" % region
            logger.debug(msg, exc_info=True)
            return HttpResponseBadRequest(msg)
    else:
        return HttpResponseBadRequest("tile or region argument required")

    jpeg_data = img.renderJpegRegion(
        z, t, x, y, w, h, level=level, compression=compress_quality
    )
    if jpeg_data is None:
        raise Http404

    rsp = HttpResponse(jpeg_data, content_type="image/jpeg")
    return rsp


@login_required()
def render_image(request, iid, z=None, t=None, conn=None, **kwargs):
    """
    Renders the image with id {{iid}} at {{z}} and {{t}} as jpeg.
    Many options are available from the request dict. See
    L{getImgDetailsFromReq} for list.
    I am assuming a single Pixels object on image with image-Id='iid'. May be
    wrong

    @param request:     http request
    @param iid:         image ID
    @param z:           Z index
    @param t:           T index
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @return:            http response wrapping jpeg
    """
    server_id = request.session["connector"]["server_id"]

    pi = _get_prepared_image(request, iid, server_id=server_id, conn=conn)
    if pi is None:
        raise Http404
    img, compress_quality = pi
    jpeg_data = img.renderJpeg(z, t, compression=compress_quality)
    if jpeg_data is None:
        raise Http404

    format = request.GET.get("format", "jpeg")
    rsp = HttpResponse(jpeg_data, content_type="image/jpeg")
    if "download" in kwargs and kwargs["download"]:
        if format == "png":
            # convert jpeg data to png...
            i = Image.open(BytesIO(jpeg_data))
            output = BytesIO()
            i.save(output, "png")
            jpeg_data = output.getvalue()
            output.close()
            rsp = HttpResponse(jpeg_data, content_type="image/png")
        elif format == "tif":
            # convert jpeg data to TIFF
            i = Image.open(BytesIO(jpeg_data))
            output = BytesIO()
            i.save(output, "tiff")
            jpeg_data = output.getvalue()
            output.close()
            rsp = HttpResponse(jpeg_data, content_type="image/tiff")
        fileName = img.getName()
        try:
            fileName = fileName.decode("utf8")
        except AttributeError:
            pass  # python 3
        fileName = fileName.replace(",", ".").replace(" ", "_")
        rsp["Content-Type"] = "application/force-download"
        rsp["Content-Length"] = len(jpeg_data)
        rsp["Content-Disposition"] = "attachment; filename=%s.%s" % (fileName, format)
    return rsp


@login_required()
@validate_rdef_query
def render_image_rdef(request, iid, z=None, t=None, conn=None, **kwargs):
    return render_image(request, iid, z=z, t=t, conn=conn, **kwargs)


@login_required()
@validate_rdef_query
def render_image_region_rdef(request, iid, z=None, t=None, conn=None, **kwargs):
    return render_image_region(request, iid, z, t, conn=conn, **kwargs)


@login_required()
def render_ome_tiff(request, ctx, cid, conn=None, **kwargs):
    """
    Renders the OME-TIFF representation of the image(s) with id cid in ctx
    (i)mage, (d)ataset, or (p)roject.
    For multiple images export, images that require pixels pyramid (big
    images) will be silently skipped.
    If exporting a single big image or if all images in a multple image export
    are big, a 404 will be triggered.
    A request parameter dryrun can be passed to return the count of images
    that would actually be exported.

    @param request:     http request
    @param ctx:         'p' or 'd' or 'i'
    @param cid:         Project, Dataset or Image ID
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @return:            http response wrapping the tiff (or zip for multiple
                        files), or redirect to temp file/zip
                        if dryrun is True, returns count of images that would
                        be exported
    """
    imgs = []
    if ctx == "p":
        obj = conn.getObject("Project", cid)
        if obj is None:
            raise Http404
        for d in obj.listChildren():
            imgs.extend(list(d.listChildren()))
        name = obj.getName()
    elif ctx == "d":
        obj = conn.getObject("Dataset", cid)
        if obj is None:
            raise Http404
        imgs.extend(list(obj.listChildren()))
        selection = list(filter(None, request.GET.get("selection", "").split(",")))
        if len(selection) > 0:
            logger.debug(selection)
            logger.debug(imgs)
            imgs = [x for x in imgs if str(x.getId()) in selection]
            logger.debug(imgs)
            if len(imgs) == 0:
                raise Http404
        name = "%s-%s" % (obj.getParent().getName(), obj.getName())
    elif ctx == "w":
        obj = conn.getObject("Well", cid)
        if obj is None:
            raise Http404
        imgs.extend([x.getImage() for x in obj.listChildren()])
        plate = obj.getParent()
        coord = "%s%s" % (
            plate.getRowLabels()[obj.row],
            plate.getColumnLabels()[obj.column],
        )
        name = "%s-%s-%s" % (plate.getParent().getName(), plate.getName(), coord)
    else:
        obj = conn.getObject("Image", cid)
        if obj is None:
            raise Http404
        imgs.append(obj)

    imgs = [x for x in imgs if not x.requiresPixelsPyramid()]

    if request.GET.get("dryrun", False):
        rv = json.dumps(len(imgs))
        c = request.GET.get("callback", None)
        if c is not None and not kwargs.get("_internal", False):
            rv = "%s(%s)" % (c, rv)
        return HttpJavascriptResponse(rv)
    if len(imgs) == 0:
        raise Http404
    if len(imgs) == 1:
        obj = imgs[0]
        key = (
            "_".join((str(x.getId()) for x in obj.getAncestry()))
            + "_"
            + str(obj.getId())
            + "_ome_tiff"
        )
        # total name len <= 255, 9 is for .ome.tiff
        fnamemax = 255 - len(str(obj.getId())) - 10
        objname = obj.getName()[:fnamemax]
        fpath, rpath, fobj = webgateway_tempfile.new(
            str(obj.getId()) + "-" + objname + ".ome.tiff", key=key
        )
        if fobj is True:
            # already exists
            return HttpResponseRedirect(
                settings.STATIC_URL + "webgateway/tfiles/" + rpath
            )
        try:
            tiff_data = imgs[0].exportOmeTiff()
        except Exception:
            logger.debug("Failed to export image (2)", exc_info=True)
            tiff_data = None
        if tiff_data is None:
            webgateway_tempfile.abort(fpath)
            raise Http404
        if fobj is None:
            rsp = HttpResponse(tiff_data, content_type="image/tiff")
            rsp["Content-Disposition"] = 'attachment; filename="%s.ome.tiff"' % (
                str(obj.getId()) + "-" + objname
            )
            rsp["Content-Length"] = len(tiff_data)
            return rsp
        else:
            fobj.write(tiff_data)
            fobj.close()
            return HttpResponseRedirect(
                settings.STATIC_URL + "webgateway/tfiles/" + rpath
            )
    else:
        try:
            img_ids = "+".join((str(x.getId()) for x in imgs)).encode("utf-8")
            key = (
                "_".join((str(x.getId()) for x in imgs[0].getAncestry()))
                + "_"
                + md5(img_ids).hexdigest()
                + "_ome_tiff_zip"
            )
            fpath, rpath, fobj = webgateway_tempfile.new(name + ".zip", key=key)
            if fobj is True:
                return HttpResponseRedirect(
                    settings.STATIC_URL + "webgateway/tfiles/" + rpath
                )
            logger.debug(fpath)
            if fobj is None:
                fobj = BytesIO()
            zobj = zipfile.ZipFile(fobj, "w", zipfile.ZIP_STORED)
            for obj in imgs:
                tiff_data = obj.exportOmeTiff()
                if tiff_data is None:
                    continue
                # While ZIP itself doesn't have the 255 char limit for
                # filenames, the FS where these get unarchived might, so trim
                # names
                # total name len <= 255, 9 is for .ome.tiff
                fnamemax = 255 - len(str(obj.getId())) - 10
                objname = obj.getName()[:fnamemax]
                zobj.writestr(str(obj.getId()) + "-" + objname + ".ome.tiff", tiff_data)
            zobj.close()
            if fpath is None:
                zip_data = fobj.getvalue()
                rsp = HttpResponse(zip_data, content_type="application/zip")
                rsp["Content-Disposition"] = 'attachment; filename="%s.zip"' % name
                rsp["Content-Length"] = len(zip_data)
                return rsp
        except Exception:
            logger.debug(traceback.format_exc())
            raise
        return HttpResponseRedirect(settings.STATIC_URL + "webgateway/tfiles/" + rpath)


@login_required()
def render_movie(request, iid, axis, pos, conn=None, **kwargs):
    """
    Renders a movie from the image with id iid

    @param request:     http request
    @param iid:         Image ID
    @param axis:        Movie frames are along 'z' or 't' dimension. String
    @param pos:         The T index (for z axis) or Z index (for t axis)
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @return:            http response wrapping the file, or redirect to temp
                        file
    """
    server_id = request.session["connector"]["server_id"]
    try:
        # Prepare a filename we'll use for temp cache, and check if file is
        # already there
        opts = {}
        opts["format"] = "video/" + request.GET.get("format", "quicktime")
        opts["fps"] = int(request.GET.get("fps", 4))
        opts["minsize"] = (512, 512, "Black")
        ext = ".avi"
        key = "%s-%s-%s-%d-%s-%s" % (
            iid,
            axis,
            pos,
            opts["fps"],
            _get_signature_from_request(request),
            request.GET.get("format", "quicktime"),
        )

        pos = int(pos)
        pi = _get_prepared_image(request, iid, server_id=server_id, conn=conn)
        if pi is None:
            raise Http404
        img, compress_quality = pi

        fpath, rpath, fobj = webgateway_tempfile.new(img.getName() + ext, key=key)
        logger.debug(fpath, rpath, fobj)
        if fobj is True:
            return HttpResponseRedirect(
                settings.STATIC_URL + "webgateway/tfiles/" + rpath
            )
            # os.path.join(rpath, img.getName() + ext))

        if "optsCB" in kwargs:
            opts.update(kwargs["optsCB"](img))
        opts.update(kwargs.get("opts", {}))
        logger.debug(
            "rendering movie for img %s with axis %s, pos %i and opts %s"
            % (iid, axis, pos, opts)
        )
        # fpath, rpath = webgateway_tempfile.newdir()
        if fpath is None:
            fo, fn = tempfile.mkstemp()
        else:
            fn = fpath  # os.path.join(fpath, img.getName())
        if axis.lower() == "z":
            dext, mimetype = img.createMovie(
                fn, 0, img.getSizeZ() - 1, pos - 1, pos - 1, opts
            )
        else:
            dext, mimetype = img.createMovie(
                fn, pos - 1, pos - 1, 0, img.getSizeT() - 1, opts
            )
        if dext is None and mimetype is None:
            # createMovie is currently only available on 4.1_custom
            # https://trac.openmicroscopy.org/ome/ticket/3857
            raise Http404
        if fpath is None:
            movie = open(fn).read()
            os.close(fo)
            rsp = HttpResponse(movie, content_type=mimetype)
            rsp["Content-Disposition"] = 'attachment; filename="%s"' % (
                img.getName() + ext
            )
            rsp["Content-Length"] = len(movie)
            return rsp
        else:
            fobj.close()
            # shutil.move(fn, fn + ext)
            return HttpResponseRedirect(
                settings.STATIC_URL + "webgateway/tfiles/" + rpath
            )
            # os.path.join(rpath, img.getName() + ext))
    except Exception:
        logger.debug(traceback.format_exc())
        raise


@login_required()
def render_split_channel(request, iid, z, t, conn=None, **kwargs):
    """
    Renders a split channel view of the image with id {{iid}} at {{z}} and
    {{t}} as jpeg.
    Many options are available from the request dict.
    Requires Pillow to be installed on the server.

    @param request:     http request
    @param iid:         Image ID
    @param z:           Z index
    @param t:           T index
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @return:            http response wrapping a jpeg
    """
    server_id = request.session["connector"]["server_id"]
    pi = _get_prepared_image(request, iid, server_id=server_id, conn=conn)
    if pi is None:
        raise Http404
    img, compress_quality = pi
    compress_quality = compress_quality and float(compress_quality) or 0.9
    jpeg_data = img.renderSplitChannel(z, t, compression=compress_quality)
    if jpeg_data is None:
        raise Http404
    rsp = HttpResponse(jpeg_data, content_type="image/jpeg")
    return rsp


def debug(f):
    """
    Decorator for adding debugging functionality to methods.

    @param f:       The function to wrap
    @return:        The wrapped function
    """

    @wraps(f)
    def wrap(request, *args, **kwargs):
        debug = request.GET.getlist("debug")
        if "slow" in debug:
            time.sleep(5)
        if "fail" in debug:
            raise Http404
        if "error" in debug:
            raise AttributeError("Debug requested error")
        return f(request, *args, **kwargs)

    return wrap


def jsonp(f):
    """
    Decorator for adding connection debugging and returning function result as
    json, depending on values in kwargs

    @param f:       The function to wrap
    @return:        The wrapped function, which will return json
    """

    @wraps(f)
    def wrap(request, *args, **kwargs):
        logger.debug("jsonp")
        try:
            server_id = kwargs.get("server_id", None)
            if server_id is None and request.session.get("connector"):
                server_id = request.session["connector"]["server_id"]
            kwargs["server_id"] = server_id
            rv = f(request, *args, **kwargs)
            if kwargs.get("_raw", False):
                return rv
            if isinstance(rv, HttpResponse):
                return rv
            c = request.GET.get("callback", None)
            if c is not None and not kwargs.get("_internal", False):
                if not VALID_JS_VARIABLE.match(c):
                    return HttpResponseBadRequest("Invalid callback")
                rv = json.dumps(rv)
                rv = "%s(%s)" % (c, rv)
                # mimetype for JSONP is application/javascript
                return HttpJavascriptResponse(rv)
            if kwargs.get("_internal", False):
                return rv
            # mimetype for JSON is application/json
            # NB: To support old api E.g. /get_rois_json/
            # We need to support lists
            safe = type(rv) is dict
            # Allow optional JSON dumps parameters
            json_params = kwargs.get("_json_dumps_params", None)
            return JsonResponse(rv, safe=safe, json_dumps_params=json_params)
        except Exception as ex:
            # Default status is 500 'server error'
            # But we try to handle all 'expected' errors appropriately
            # TODO: handle omero.ConcurrencyException
            status = 500
            if isinstance(ex, omero.SecurityViolation):
                status = 403
            elif isinstance(ex, omero.ApiUsageException):
                status = 400
            trace = traceback.format_exc()
            logger.debug(trace)
            if kwargs.get("_raw", False) or kwargs.get("_internal", False):
                raise
            return JsonResponse(
                {"message": str(ex), "stacktrace": trace}, status=status
            )

    return wrap


@debug
@login_required()
def render_row_plot(request, iid, z, t, y, conn=None, w=1, **kwargs):
    """
    Renders the line plot for the image with id {{iid}} at {{z}} and {{t}} as
    gif with transparent background.
    Many options are available from the request dict.
    I am assuming a single Pixels object on image with Image ID='iid'. May be
    wrong
    TODO: cache

    @param request:     http request
    @param iid:         Image ID
    @param z:           Z index
    @param t:           T index
    @param y:           Y position of row to measure
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @param w:           Line width
    @return:            http response wrapping a gif
    """

    if not w:
        w = 1
    pi = _get_prepared_image(request, iid, conn=conn)
    if pi is None:
        raise Http404
    img, compress_quality = pi
    try:
        gif_data = img.renderRowLinePlotGif(int(z), int(t), int(y), int(w))
    except Exception:
        logger.debug("a", exc_info=True)
        raise
    if gif_data is None:
        raise Http404
    rsp = HttpResponse(gif_data, content_type="image/gif")
    return rsp


@debug
@login_required()
def render_col_plot(request, iid, z, t, x, w=1, conn=None, **kwargs):
    """
    Renders the line plot for the image with id {{iid}} at {{z}} and {{t}} as
    gif with transparent background.
    Many options are available from the request dict.
    I am assuming a single Pixels object on image with id='iid'. May be wrong
    TODO: cache

    @param request:     http request
    @param iid:         Image ID
    @param z:           Z index
    @param t:           T index
    @param x:           X position of column to measure
    @param conn:        L{omero.gateway.BlitzGateway} connection
    @param w:           Line width
    @return:            http response wrapping a gif
    """

    if not w:
        w = 1
    pi = _get_prepared_image(request, iid, conn=conn)
    if pi is None:
        raise Http404
    img, compress_quality = pi
    gif_data = img.renderColLinePlotGif(int(z), int(t), int(x), int(w))
    if gif_data is None:
        raise Http404
    rsp = HttpResponse(gif_data, content_type="image/gif")
    return rsp


@login_required()
@jsonp
def imageData_json(request, conn=None, _internal=False, **kwargs):
    """
    Get a dict with image information
    TODO: cache

    @param request:     http request
    @param conn:        L{omero.gateway.BlitzGateway}
    @param _internal:   TODO: ?
    @return:            Dict
    """

    iid = kwargs["iid"]
    key = kwargs.get("key", None)
    image = conn.getObject("Image", iid)
    if image is None:
        if is_public_user(request):
            # 403 - Should try logging in
            return HttpResponseForbidden()
        else:
            return HttpResponseNotFound("Image:%s not found" % iid)
    if request.GET.get("getDefaults") == "true":
        image.resetDefaults(save=False)
    rv = imageMarshal(image, key=key, request=request)
    return rv


@login_required()
@jsonp
def wellData_json(request, conn=None, _internal=False, **kwargs):
    """
    Get a dict with image information
    TODO: cache

    @param request:     http request
    @param conn:        L{omero.gateway.BlitzGateway}
    @param _internal:   TODO: ?
    @return:            Dict
    """

    wid = kwargs["wid"]
    well = conn.getObject("Well", wid)
    if well is None:
        return HttpJavascriptResponseServerError('""')
    prefix = kwargs.get("thumbprefix", "webgateway_render_thumbnail")

    def urlprefix(iid):
        return reverse(prefix, args=(iid,))

    xtra = {"thumbUrlPrefix": kwargs.get("urlprefix", urlprefix)}
    rv = well.simpleMarshal(xtra=xtra)
    return rv


@login_required()
@jsonp
def plateGrid_json(request, pid, field=0, acquisition=None, conn=None, **kwargs):
    """
    Layout depends on settings 'omero.web.plate_layout' which
    can be overridden with request param e.g. ?layout=shrink.
    Use "expand" to expand to multiple of 8 x 12 grid
    Or "shrink" to remove rows/cols before first Well
    Or "trim" to neither expand nor shrink
    """
    try:
        field = int(field or 0)
    except ValueError:
        field = 0

    if acquisition is not None:
        try:
            acquisition = int(acquisition)
        except ValueError:
            acquisition = None

    prefix = kwargs.get("thumbprefix", "webgateway_render_thumbnail")
    thumbsize = getIntOrDefault(request, "size", None)
    logger.debug(thumbsize)

    def get_thumb_url(iid):
        if thumbsize is not None:
            return reverse(prefix, args=(iid, thumbsize))
        return reverse(prefix, args=(iid,))

    layout = request.GET.get("layout")
    if layout not in ("shrink", "trim", "expand"):
        layout = settings.PLATE_LAYOUT

    plateGrid = PlateGrid(
        conn,
        pid,
        field,
        thumbprefix=kwargs.get("urlprefix", get_thumb_url),
        plate_layout=layout,
        acqid=acquisition,
    )

    plate = plateGrid.plate
    if plate is None:
        return Http404

    rv = plateGrid.metadata
    return rv


@login_required()
@jsonp
def get_thumbnails_json(request, w=None, conn=None, **kwargs):
    """
    Returns base64 encoded jpeg with the rendered thumbnail for images
    'id'

    @param request:     http request
    @param w:           Thumbnail max width. 96 by default
    @return:            http response containing base64 encoded thumbnails
    """
    server_settings = request.session.get("server_settings", {}).get("browser", {})
    defaultSize = server_settings.get("thumb_default_size", 96)
    if w is None:
        w = defaultSize
    image_ids = get_longs(request, "id")
    image_ids = list(set(image_ids))  # remove any duplicates
    # If we only have a single ID, simply use getThumbnail()
    if len(image_ids) == 1:
        iid = image_ids[0]
        try:
            data = _render_thumbnail(request, iid, w=w, conn=conn)
            return {
                iid: "data:image/jpeg;base64,%s"
                % base64.b64encode(data).decode("utf-8")
            }
        except Exception:
            return {iid: None}
    logger.debug("Image ids: %r" % image_ids)
    if len(image_ids) > settings.THUMBNAILS_BATCH:
        return HttpJavascriptResponseServerError(
            "Max %s thumbnails at a time." % settings.THUMBNAILS_BATCH
        )
    thumbnails = conn.getThumbnailSet([rlong(i) for i in image_ids], w)
    rv = dict()
    for i in image_ids:
        rv[i] = None
        try:
            t = thumbnails[i]
            if len(t) > 0:
                # replace thumbnail urls by base64 encoded image
                rv[i] = "data:image/jpeg;base64,%s" % base64.b64encode(t).decode(
                    "utf-8"
                )
        except KeyError:
            logger.error("Thumbnail not available. (img id: %d)" % i)
        except Exception:
            logger.error(traceback.format_exc())
    return rv


@login_required()
@jsonp
def get_thumbnail_json(request, iid, w=None, h=None, conn=None, _defcb=None, **kwargs):
    """
    Returns an HttpResponse base64 encoded jpeg with the rendered thumbnail
    for image 'iid'

    @param request:     http request
    @param iid:         Image ID
    @param w:           Thumbnail max width. 96 by default
    @param h:           Thumbnail max height
    @return:            http response containing base64 encoded thumbnail
    """
    jpeg_data = _render_thumbnail(
        request=request, iid=iid, w=w, h=h, conn=conn, _defcb=_defcb, **kwargs
    )
    rv = "data:image/jpeg;base64,%s" % base64.b64encode(jpeg_data).decode("utf-8")
    return rv


@login_required()
@jsonp
def listImages_json(request, did, conn=None, **kwargs):
    """
    lists all Images in a Dataset, as json
    TODO: cache

    @param request:     http request
    @param did:         Dataset ID
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            list of image json.
    """

    dataset = conn.getObject("Dataset", did)
    if dataset is None:
        return HttpJavascriptResponseServerError('""')
    prefix = kwargs.get("thumbprefix", "webgateway_render_thumbnail")

    def urlprefix(iid):
        return reverse(prefix, args=(iid,))

    xtra = {
        "thumbUrlPrefix": kwargs.get("urlprefix", urlprefix),
        "tiled": request.GET.get("tiled", False),
    }
    return [x.simpleMarshal(xtra=xtra) for x in dataset.listChildren()]


@login_required()
@jsonp
def listWellImages_json(request, did, conn=None, **kwargs):
    """
    lists all Images in a Well, as json
    TODO: cache

    @param request:     http request
    @param did:         Well ID
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            list of image json.
    """

    well = conn.getObject("Well", did)
    acq = getIntOrDefault(request, "run", None)
    if well is None:
        return HttpJavascriptResponseServerError('""')
    prefix = kwargs.get("thumbprefix", "webgateway_render_thumbnail")

    def urlprefix(iid):
        return reverse(prefix, args=(iid,))

    xtra = {"thumbUrlPrefix": kwargs.get("urlprefix", urlprefix)}

    def marshal_pos(w):
        d = {}
        for x, p in (["x", w.getPosX()], ["y", w.getPosY()]):
            if p is not None:
                d[x] = {"value": p.getValue(), "unit": str(p.getUnit())}
        return d

    plate = well.getParent()
    run_d = {r.getId(): r.getName() for r in plate.listPlateAcquisitions()}
    wellImgs = []
    for ws in well.listChildren():
        # optionally filter by acquisition 'run'
        if (
            acq is not None
            and ws.plateAcquisition is not None
            and ws.plateAcquisition.id.val != acq
        ):
            continue
        img = ws.getImage()
        if img is not None:
            m = img.simpleMarshal(xtra=xtra)
            pos = marshal_pos(ws)
            if len(pos.keys()) > 0:
                m["position"] = pos
            if ws.plateAcquisition is not None:
                m["name"] += f" [Run: {run_d[ws.plateAcquisition._id._val]}]"
            wellImgs.append(m)
    return wellImgs


@login_required()
@jsonp
def listDatasets_json(request, pid, conn=None, **kwargs):
    """
    lists all Datasets in a Project, as json
    TODO: cache

    @param request:     http request
    @param pid:         Project ID
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            list of dataset json.
    """

    project = conn.getObject("Project", pid)
    if project is None:
        return HttpJavascriptResponse("[]")
    return [x.simpleMarshal(xtra={"childCount": 0}) for x in project.listChildren()]


@login_required()
@jsonp
def datasetDetail_json(request, did, conn=None, **kwargs):
    """
    return json encoded details for a dataset
    TODO: cache
    """
    ds = conn.getObject("Dataset", did)
    return ds.simpleMarshal()


@login_required()
@jsonp
def listProjects_json(request, conn=None, **kwargs):
    """
    lists all Projects, as json
    TODO: cache

    @param request:     http request
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            list of project json.
    """

    rv = []
    for pr in conn.listProjects():
        rv.append({"id": pr.id, "name": pr.name, "description": pr.description or ""})
    return rv


@login_required()
@jsonp
def projectDetail_json(request, pid, conn=None, **kwargs):
    """
    grab details from one specific project
    TODO: cache

    @param request:     http request
    @param pid:         Project ID
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            project details as dict.
    """

    pr = conn.getObject("Project", pid)
    rv = pr.simpleMarshal()
    return rv


@jsonp
def open_with_options(request, **kwargs):
    """
    Make the settings.OPEN_WITH available via JSON
    """
    open_with = settings.OPEN_WITH
    viewers = []
    for ow in open_with:
        if len(ow) < 2:
            continue
        viewer = {}
        viewer["id"] = ow[0]
        try:
            viewer["url"] = reverse(ow[1])
        except NoReverseMatch:
            viewer["url"] = ow[1]
        # try non-essential parameters...
        # NB: Need supported_objects OR script_url to enable plugin
        try:
            if len(ow) > 2:
                if "supported_objects" in ow[2]:
                    viewer["supported_objects"] = ow[2]["supported_objects"]
                if "target" in ow[2]:
                    viewer["target"] = ow[2]["target"]
                if "script_url" in ow[2]:
                    # If we have an absolute url, use it...
                    if ow[2]["script_url"].startswith("http"):
                        viewer["script_url"] = ow[2]["script_url"]
                    else:
                        # ...otherwise, assume within static
                        viewer["script_url"] = static(ow[2]["script_url"])
                if "label" in ow[2]:
                    viewer["label"] = ow[2]["label"]
        except Exception:
            # ignore invalid params
            pass
        viewers.append(viewer)
    return {"open_with_options": viewers}


def searchOptFromRequest(request):
    """
    Returns a dict of options for searching, based on
    parameters in the http request
    Request keys include:
        - ctx: (http request) 'imgs' to search only images
        - text: (http request) the actual text phrase
        - start: starting index (0 based) for result
        - limit: nr of results to retuen (0 == unlimited)
        - author:
        - grabData:
        - parents:

    @param request:     http request
    @return:            Dict of options
    """

    try:
        r = request.GET
        opts = {
            "search": str(r.get("text", "")).encode("utf8"),
            "ctx": r.get("ctx", ""),
            "grabData": not not r.get("grabData", False),
            "parents": not not bool(r.get("parents", False)),
            "start": int(r.get("start", 0)),
            "limit": int(r.get("limit", 0)),
            "key": r.get("key", None),
        }
        author = r.get("author", "")
        if author:
            opts["search"] += " author:" + author
        return opts
    except Exception:
        logger.error(traceback.format_exc())
        return {}


@TimeIt(logging.INFO)
@login_required()
@jsonp
def search_json(request, conn=None, **kwargs):
    """
    Search for objects in blitz.
    Returns json encoded list of marshalled objects found by the search query
    Request keys include:
        - text: The text to search for
        - ctx: (http request) 'imgs' to search only images
        - text: (http request) the actual text phrase
        - start: starting index (0 based) for result
        - limit: nr of results to retuen (0 == unlimited)
        - author:
        - grabData:
        - parents:

    @param request:     http request
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            json search results
    TODO: cache
    """
    server_id = request.session["connector"]["server_id"]
    opts = searchOptFromRequest(request)
    rv = []
    logger.debug("searchObjects(%s)" % (opts["search"]))
    # search returns blitz_connector wrapper objects

    def urlprefix(iid):
        return reverse("webgateway_render_thumbnail", args=(iid,))

    xtra = {"thumbUrlPrefix": kwargs.get("urlprefix", urlprefix)}
    try:
        if opts["ctx"] == "imgs":
            sr = conn.searchObjects(["image"], opts["search"], conn.SERVICE_OPTS)
        else:
            # searches P/D/I
            sr = conn.searchObjects(None, opts["search"], conn.SERVICE_OPTS)
    except ApiUsageException:
        return HttpJavascriptResponseServerError('"parse exception"')

    def marshal():
        rv = []
        if opts["grabData"] and opts["ctx"] == "imgs":
            bottom = min(opts["start"], len(sr) - 1)
            if opts["limit"] == 0:
                top = len(sr)
            else:
                top = min(len(sr), bottom + opts["limit"])
            for i in range(bottom, top):
                e = sr[i]
                # for e in sr:
                try:
                    rv.append(
                        imageData_json(
                            request,
                            server_id,
                            iid=e.id,
                            key=opts["key"],
                            conn=conn,
                            _internal=True,
                        )
                    )
                except AttributeError as x:
                    logger.debug(
                        "(iid %i) ignoring Attribute Error: %s" % (e.id, str(x))
                    )
                    pass
                except omero.ServerError as x:
                    logger.debug("(iid %i) ignoring Server Error: %s" % (e.id, str(x)))
            return rv
        else:
            return [x.simpleMarshal(xtra=xtra, parents=opts["parents"]) for x in sr]

    rv = timeit(marshal)()
    logger.debug(rv)
    return rv


@require_POST
@login_required()
@validate_rdef_query
def save_image_rdef_json(request, iid, conn=None, **kwargs):
    """
    Requests that the rendering defs passed in the request be set as the
    default for this image.
    Rendering defs in request listed at L{getImgDetailsFromReq}
    TODO: jsonp

    @param request:     http request
    @param iid:         Image ID
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            http response 'true' or 'false'
    """
    server_id = request.session["connector"]["server_id"]

    pi = _get_prepared_image(
        request, iid, server_id=server_id, conn=conn, saveDefs=True
    )
    if pi is None:
        json_data = "false"
    else:
        pi[0].getThumbnail()
        json_data = "true"
    if request.GET.get("callback", None):
        json_data = "%s(%s)" % (request.GET["callback"], json_data)
    return HttpJavascriptResponse(json_data)


@login_required()
@jsonp
def listLuts_json(request, conn=None, **kwargs):
    """
    Lists lookup tables 'LUTs' availble for rendering.

    We include 'png_index' which is the index of each LUT within the
    static/webgateway/img/luts_10.png or -1 if LUT is not found.

    Since 5.28.0, the list of LUTs is also generated dynamically.
    The new LUT indexes and LUT list were added to
    the response with the suffix '_new' (png_index_new and png_luts_new)
    The png matching the new indexes and list of LUT is obtained from
    this url: /webgateway/luts_png/   (views.luts_png)
    """
    scriptService = conn.getScriptService()
    luts = scriptService.getScriptsByMimetype("text/x-lut")
    luts.sort(key=lambda x: x.name.val.lower())
    rv, all_luts = [], []
    for i, lut in enumerate(luts):
        lutsrc = lut.path.val + lut.name.val
        all_luts.append(lutsrc)
        idx = LUTS_IN_PNG.index(lutsrc) if lutsrc in LUTS_IN_PNG else -1
        rv.append(
            {
                "id": lut.id.val,
                "path": lut.path.val,
                "name": lut.name.val,
                "size": unwrap(lut.size),
                "png_index": idx,
                "png_index_new": i,
            }
        )
    all_luts.append("gradient.png")

    return {"luts": rv, "png_luts": LUTS_IN_PNG, "png_luts_new": all_luts}


@login_required()
def luts_png(request, conn=None, **kwargs):
    """
    Generates the LUT png used for preview and selection of LUT. The png is
    256px wide, and each LUT is 10px in height. The last portion of the png
    is the channel sliders transparent gradient.

    LUTs are listed in alphabetical order (lut name only from filename).

    LUT files on the server are read with the script service, and
    file content is parsed with a custom implementation.

    This uses caching to prevent generating the png each time a LUT
    menu is opened. The cache key is a hash of all LUTs path.
    Change in the LUT name or path will force the generation of a new
    png.
    """
    scriptService = conn.getScriptService()
    luts = scriptService.getScriptsByMimetype("text/x-lut")
    luts.sort(key=lambda x: x.name.val)
    luts_path = []
    for lut in luts:
        luts_path.append(lut.path.val + lut.name.val)
    luts_hash = hash("\n".join(luts_path))
    cache_key = f"lut_hash_{luts_hash}"

    cached_image = cache.get(cache_key)
    if cached_image:
        return HttpResponse(cached_image, content_type="image/png")

    # Generate the LUT, fourth png channel set to 255
    new_img = numpy.zeros((10 * (len(luts) + 1), 256, 4), dtype="uint8") + 255
    for i, lut in enumerate(luts):
        orig_file = conn.getObject("OriginalFile", lut.getId()._val)
        lut_data = bytearray()
        # Collect the LUT data in byte form
        for chunk in orig_file.getFileInChunks():
            lut_data.extend(chunk)

        if len(lut_data) in [768, 800]:
            lut_arr = numpy.array(lut_data, dtype="uint8")[-768:]
            new_img[(i * 10) : (i + 1) * 10, :, :3] = lut_arr.reshape(3, 256).T
        else:
            lut_data = lut_data.decode()
            r, g, b = [], [], []

            lines = lut_data.split("\n")
            sep = None
            if "\t" in lines[0]:
                sep = "\t"
            for line in lines:
                val = line.split(sep)
                if len(val) < 3 or not val[-1].isnumeric():
                    continue
                r.append(int(val[-3]))
                g.append(int(val[-2]))
                b.append(int(val[-1]))
            new_img[(i * 10) : (i + 1) * 10, :, 0] = numpy.array(r)
            new_img[(i * 10) : (i + 1) * 10, :, 1] = numpy.array(g)
            new_img[(i * 10) : (i + 1) * 10, :, 2] = numpy.array(b)

    # Set the last row for the channel sliders transparent gradient
    new_img[-10:] = 0
    new_img[-10:, :180, 3] = numpy.linspace(255, 0, 180, dtype="uint8")

    image = Image.fromarray(new_img)
    # Save the image to a BytesIO stream
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Cache the image using the version-based key
    # Cache timeout set to None (no timeout)
    cache.set(cache_key, buffer.getvalue(), None)

    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required()
def list_compatible_imgs_json(request, iid, conn=None, **kwargs):
    """
    Lists the images on the same project that would be viable targets for
    copying rendering settings.
    TODO: change method to:
    list_compatible_imgs_json (request, iid, server_id=None, conn=None,
    **kwargs):

    @param request:     http request
    @param iid:         Image ID
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            json list of image IDs
    """

    json_data = "false"
    r = request.GET
    if conn is None:
        img = None
    else:
        img = conn.getObject("Image", iid)

    if img is not None:
        # List all images in project
        imgs = []
        for ds in img.getProject().listChildren():
            imgs.extend(ds.listChildren())
        # Filter the ones that would pass the applySettingsToImages call
        img_ptype = img.getPrimaryPixels().getPixelsType().getValue()
        img_ccount = img.getSizeC()
        img_ew = [x.getLabel() for x in img.getChannels()]
        img_ew.sort()

        def compat(i):
            if int(i.getId()) == int(iid):
                return False
            pp = i.getPrimaryPixels()
            if (
                pp is None
                or i.getPrimaryPixels().getPixelsType().getValue() != img_ptype
                or i.getSizeC() != img_ccount
            ):
                return False
            ew = [x.getLabel() for x in i.getChannels()]
            ew.sort()
            if ew != img_ew:
                return False
            return True

        imgs = filter(compat, imgs)
        json_data = json.dumps([x.getId() for x in imgs])

    if r.get("callback", None):
        json_data = "%s(%s)" % (r["callback"], json_data)
    return HttpJavascriptResponse(json_data)


@require_POST
@login_required()
@jsonp
def reset_rdef_json(request, toOwners=False, conn=None, **kwargs):
    """
    Simply takes request 'to_type' and 'toids' and
    delegates to Rendering Settings service to reset
    settings accordings.

    @param toOwners:    if True, default to the owner's settings.
    """

    r = request.POST
    toids = r.getlist("toids")
    to_type = str(r.get("to_type", "image"))
    to_type = to_type.title()
    if to_type == "Acquisition":
        to_type = "PlateAcquisition"

    if len(toids) == 0:
        raise Http404(
            "Need to specify objects in request, E.g."
            " ?totype=dataset&toids=1&toids=2"
        )

    toids = [int(id) for id in toids]

    rss = conn.getRenderingSettingsService()

    # get the first object and set the group to match
    conn.SERVICE_OPTS.setOmeroGroup("-1")
    o = conn.getObject(to_type, toids[0])
    if o is not None:
        gid = o.getDetails().group.id.val
        conn.SERVICE_OPTS.setOmeroGroup(gid)

    if toOwners:
        rv = rss.resetDefaultsByOwnerInSet(to_type, toids, conn.SERVICE_OPTS)
    else:
        rv = rss.resetDefaultsInSet(to_type, toids, conn.SERVICE_OPTS)

    return rv


# maybe these pair of methods should be on ImageWrapper??
def getRenderingSettings(image):
    rv = {}
    chs = []
    maps = []
    for i, ch in enumerate(image.getChannels()):
        act = "" if ch.isActive() else "-"
        start = ch.getWindowStart()
        end = ch.getWindowEnd()
        color = ch.getLut()
        maps.append(
            {
                "inverted": {"enabled": ch.isInverted()},
                "quantization": {
                    "coefficient": unwrap(ch.getCoefficient()),
                    "family": unwrap(ch.getFamily()),
                },
            }
        )
        if not color or len(color) == 0:
            color = ch.getColor().getHtml()
        chs.append("%s%s|%s:%s$%s" % (act, i + 1, start, end, color))
    rv["c"] = ",".join(chs)
    rv["maps"] = maps
    logger.info(maps)
    rv["m"] = "g" if image.isGreyscaleRenderingModel() else "c"
    rv["z"] = image.getDefaultZ() + 1
    rv["t"] = image.getDefaultT() + 1
    rv["p"] = image.getProjection()
    return rv


def applyRenderingSettings(image, rdef):
    invert_flags = _get_inverted_enabled(rdef, image.getSizeC())
    channels, windows, colors = _split_channel_info(rdef["c"])
    # also prepares _re
    image.setActiveChannels(channels, windows, colors, invert_flags)
    if rdef["m"] == "g":
        image.setGreyscaleRenderingModel()
    else:
        image.setColorRenderingModel()
    if "z" in rdef:
        image._re.setDefaultZ(int(rdef["z"]) - 1)
    if "t" in rdef:
        image._re.setDefaultT(int(rdef["t"]) - 1)
    image.saveDefaults()


@login_required()
@jsonp
def copy_image_rdef_json(request, conn=None, **kwargs):
    """
    If 'fromid' is in request, copy the image ID to session,
    for applying later using this same method.
    If list of 'toids' is in request, paste the image ID from the session
    to the specified images.
    If 'fromid' AND 'toids' are in the reqest, we simply
    apply settings and don't save anything to request.
    If 'to_type' is in request, this can be 'dataset', 'plate', 'acquisition'
    Returns json dict of Boolean:[Image-IDs] for images that have successfully
    had the rendering settings applied, or not.

    @param request:     http request
    @param server_id:
    @param conn:        L{omero.gateway.BlitzGateway}
    @return:            json dict of Boolean:[Image-IDs]
    """

    json_data = False

    fromid = request.GET.get("fromid", None)
    toids = request.POST.getlist("toids")
    to_type = str(request.POST.get("to_type", "image"))
    rdef = None

    if to_type not in ("dataset", "plate", "acquisition"):
        to_type = "Image"  # default is image

    # Only 'fromid' is given, simply save to session
    if fromid is not None and len(toids) == 0:
        request.session.modified = True
        request.session["fromid"] = fromid
        if request.session.get("rdef") is not None:
            del request.session["rdef"]
        return True

    # If we've got an rdef encoded in request instead of ImageId...
    r = request.GET or request.POST
    if r.get("c") is not None:
        # make a map of settings we need
        rdef = {"c": str(r.get("c"))}  # channels
        if r.get("maps"):
            try:
                rdef["maps"] = json.loads(r.get("maps"))
            except Exception:
                pass
        if r.get("pixel_range"):
            rdef["pixel_range"] = str(r.get("pixel_range"))
        if r.get("m"):
            rdef["m"] = str(r.get("m"))  # model (grey)
        if r.get("z"):
            rdef["z"] = str(r.get("z"))  # z & t pos
        if r.get("t"):
            rdef["t"] = str(r.get("t"))
        imageId = request.GET.get("imageId", request.POST.get("imageId", None))
        if imageId:
            rdef["imageId"] = int(imageId)

        if request.method == "GET":
            request.session.modified = True
            request.session["rdef"] = rdef
            # remove any previous rdef we may have via 'fromId'
            if request.session.get("fromid") is not None:
                del request.session["fromid"]
            return True

    # Check session for 'fromid'
    if fromid is None:
        fromid = request.session.get("fromid", None)

    # Use rdef from above or previously saved one...
    if rdef is None:
        rdef = request.session.get("rdef")
    if request.method == "POST":
        originalSettings = None
        fromImage = None
        if fromid is None:
            # if we have rdef, save to source image, then use that image as
            # 'fromId', then revert.
            if rdef is not None and len(toids) > 0:
                fromImage = conn.getObject("Image", rdef["imageId"])
                if fromImage is not None:
                    # copy orig settings
                    originalSettings = getRenderingSettings(fromImage)
                    applyRenderingSettings(fromImage, rdef)
                    fromid = fromImage.getId()

        # If we have both, apply settings...
        try:
            fromid = int(fromid)
            toids = [int(x) for x in toids]
        except TypeError:
            fromid = None
        except ValueError:
            fromid = None
        if fromid is not None and len(toids) > 0:
            json_data = conn.applySettingsToSet(fromid, to_type, toids)

        # finally - if we temporarily saved rdef to original image, revert
        # if we're sure that from-image is not in the target set (Dataset etc)
        if to_type == "Image" and fromid not in toids:
            if originalSettings is not None and fromImage is not None:
                applyRenderingSettings(fromImage, originalSettings)
        return json_data

    else:
        return HttpResponseNotAllowed(["POST"])


@login_required()
@jsonp
def get_image_rdef_json(request, conn=None, **kwargs):
    """
    Gets any 'rdef' dict from the request.session and
    returns it as json
    """
    rdef = request.session.get("rdef")
    image = None
    if rdef is None:
        fromid = request.session.get("fromid", None)
        if fromid is not None:
            # We only have an Image to copy rdefs from
            image = conn.getObject("Image", fromid)
        if image is not None:
            rv = imageMarshal(image, request=request)
            chs = []
            maps = []
            for i, ch in enumerate(rv["channels"]):
                act = ch["active"] and str(i + 1) or "-%s" % (i + 1)
                color = ch.get("lut") or ch["color"]
                chs.append(
                    "%s|%s:%s$%s"
                    % (act, ch["window"]["start"], ch["window"]["end"], color)
                )
                maps.append(
                    {
                        "inverted": {"enabled": ch["inverted"]},
                        "quantization": {
                            "coefficient": ch["coefficient"],
                            "family": ch["family"],
                        },
                    }
                )
            rdef = {
                "c": (",".join(chs)),
                "m": rv["rdefs"]["model"],
                "pixel_range": "%s:%s" % (rv["pixel_range"][0], rv["pixel_range"][1]),
                "maps": maps,
            }

    return {"rdef": rdef}


@login_required()
def full_viewer(request, iid, conn=None, **kwargs):
    """
    This view is responsible for showing the omero_image template
    Image rendering options in request are used in the display page. See
    L{getImgDetailsFromReq}.

    @param request:     http request.
    @param iid:         Image ID
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    Can be used to specify the html 'template' for
                        rendering
    @return:            html page of image and metadata
    """

    server_id = request.session["connector"]["server_id"]
    server_name = Server.get(server_id).server

    rid = getImgDetailsFromReq(request)
    server_settings = request.session.get("server_settings", {}).get("viewer", {})
    interpolate = server_settings.get("interpolate_pixels", True)
    roiLimit = server_settings.get("roi_limit", 2000)

    try:
        image = conn.getObject("Image", iid)
        if image is None:
            logger.debug("(a)Image %s not found..." % (str(iid)))
            raise Http404

        opengraph = None
        twitter = None
        image_preview = None
        page_url = None

        if hasattr(settings, "SHARING_OPENGRAPH"):
            opengraph = settings.SHARING_OPENGRAPH.get(server_name)
            logger.debug("Open Graph enabled: %s", opengraph)

        if hasattr(settings, "SHARING_TWITTER"):
            twitter = settings.SHARING_TWITTER.get(server_name)
            logger.debug("Twitter enabled: %s", twitter)

        if opengraph or twitter:
            urlargs = {"iid": iid}
            prefix = kwargs.get("thumbprefix", "webgateway_render_thumbnail")
            image_preview = request.build_absolute_uri(reverse(prefix, kwargs=urlargs))
            page_url = request.build_absolute_uri(
                reverse("webgateway_full_viewer", kwargs=urlargs)
            )

        d = {
            "blitzcon": conn,
            "image": image,
            "opts": rid,
            "interpolate": interpolate,
            "build_year": build_year,
            "roiLimit": roiLimit,
            "roiCount": image.getROICount(),
            "viewport_server": kwargs.get(
                # remove any trailing slash
                "viewport_server",
                reverse("webgateway"),
            ).rstrip("/"),
            "opengraph": opengraph,
            "twitter": twitter,
            "image_preview": image_preview,
            "page_url": page_url,
            "object": "image:%i" % int(iid),
        }

        template = kwargs.get("template", "webgateway/viewport/omero_image.html")
        rsp = render(request, template, d)
    except omero.SecurityViolation:
        logger.warn("SecurityViolation in Image:%s", iid)
        logger.warn(traceback.format_exc())
        raise Http404
    return HttpResponse(rsp)


@login_required()
def download_as(request, iid=None, conn=None, **kwargs):
    """
    Downloads the image as a single jpeg/png/tiff or as a zip (if more than
    one image)
    """
    format = request.GET.get("format", "png")
    if format not in ("jpeg", "png", "tif"):
        format = "png"

    imgIds = []
    wellIds = []
    if iid is None:
        imgIds = request.GET.getlist("image")
        if len(imgIds) == 0:
            wellIds = request.GET.getlist("well")
            if len(wellIds) == 0:
                return HttpResponseServerError(
                    "No images or wells specified in request."
                    " Use ?image=123 or ?well=123"
                )
    else:
        imgIds = [iid]

    images = []
    if imgIds:
        images = list(conn.getObjects("Image", imgIds))
    elif wellIds:
        try:
            index = int(request.GET.get("index", 0))
        except ValueError:
            index = 0
        for w in conn.getObjects("Well", wellIds):
            images.append(w.getWellSample(index).image())

    if len(images) == 0:
        msg = "Cannot download as %s. Images (ids: %s) not found." % (format, imgIds)
        logger.debug(msg)
        return HttpResponseServerError(msg)

    if len(images) == 1:
        # not expected, as download_placeholder is for multiple images
        return render_image(request, images[0].id, conn=conn, download=True)
    else:
        temp = tempfile.NamedTemporaryFile(suffix=".download_as")

        def makeImageName(originalName, extension, folder_name):
            name = os.path.basename(originalName)
            imgName = "%s.%s" % (name, extension)
            imgName = os.path.join(folder_name, imgName)
            # check we don't overwrite existing file
            i = 1
            name = imgName[: -(len(extension) + 1)]
            while os.path.exists(imgName):
                imgName = "%s_(%d).%s" % (name, i, extension)
                i += 1
            return imgName

        try:
            temp_zip_dir = tempfile.mkdtemp()
            logger.debug("download_as dir: %s" % temp_zip_dir)
            try:
                for img in images:
                    z = t = None
                    try:
                        pilImg = img.renderImage(z, t)
                        imgPathName = makeImageName(img.getName(), format, temp_zip_dir)
                        pilImg.save(imgPathName)
                    finally:
                        # Close RenderingEngine
                        img._re.close()
                # create zip
                zip_file = zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED)
                try:
                    a_files = os.path.join(temp_zip_dir, "*")
                    for name in glob.glob(a_files):
                        zip_file.write(name, os.path.basename(name))
                finally:
                    zip_file.close()
            finally:
                shutil.rmtree(temp_zip_dir, ignore_errors=True)

            zipName = request.GET.get("zipname", "Download_as_%s" % format)
            zipName = zipName.replace(" ", "_")
            if not zipName.endswith(".zip"):
                zipName = "%s.zip" % zipName

            # return the zip or single file
            rsp = StreamingHttpResponse(FileWrapper(temp))
            rsp["Content-Length"] = temp.tell()
            rsp["Content-Disposition"] = "attachment; filename=%s" % zipName
            temp.seek(0)

        except Exception:
            temp.close()
            stack = traceback.format_exc()
            logger.error(stack)
            return HttpResponseServerError("Cannot download file (id:%s)" % iid)

    rsp["Content-Type"] = "application/force-download"
    return rsp


@login_required(doConnectionCleanup=False)
def archived_files(request, iid=None, conn=None, **kwargs):
    """
    Downloads the archived file(s) as a single file or as a zip (if more than
    one file)
    """

    imgIds = []
    wellIds = []
    imgIds = request.GET.getlist("image")
    wellIds = request.GET.getlist("well")
    if iid is None:
        if len(imgIds) == 0 and len(wellIds) == 0:
            return HttpResponseServerError(
                "No images or wells specified in request."
                " Use ?image=123 or ?well=123"
            )
    else:
        imgIds = [iid]

    images = list()
    wells = list()
    if imgIds:
        images = list(conn.getObjects("Image", imgIds))
    elif wellIds:
        try:
            index = int(request.GET.get("index", 0))
        except ValueError:
            index = 0
        wells = conn.getObjects("Well", wellIds)
        for w in wells:
            images.append(w.getWellSample(index).image())
    if len(images) == 0:
        message = (
            "Cannot download archived file because Images not "
            "found (ids: %s)" % (imgIds)
        )
        logger.debug(message)
        return HttpResponseServerError(message)

    # Test permissions on images and weels
    for ob in wells:
        if hasattr(ob, "canDownload"):
            if not ob.canDownload():
                return HttpResponseNotFound()

    for ob in images:
        well = None
        try:
            well = ob.getParent().getParent()
        except Exception:
            if hasattr(ob, "canDownload"):
                if not ob.canDownload():
                    return HttpResponseNotFound()
        else:
            if well and isinstance(well, omero.gateway.WellWrapper):
                if hasattr(well, "canDownload"):
                    if not well.canDownload():
                        return HttpResponseNotFound()

    # make list of all files, removing duplicates
    fileMap = {}
    for image in images:
        for f in image.getImportedImageFiles():
            fileMap[f.getId()] = f
    files = list(fileMap.values())

    if len(files) == 0:
        message = (
            "Tried downloading archived files from image with no" " files archived."
        )
        logger.debug(message)
        return HttpResponseServerError(message)

    if len(files) == 1:
        orig_file = files[0]
        rsp = ConnCleaningHttpResponse(
            orig_file.getFileInChunks(buf=settings.CHUNK_SIZE)
        )
        rsp.conn = conn
        rsp["Content-Length"] = orig_file.getSize()
        # ',' in name causes duplicate headers
        fname = orig_file.getName().replace(" ", "_").replace(",", ".")
        rsp["Content-Disposition"] = "attachment; filename=%s" % (fname)
    else:
        total_size = sum(f.size for f in files)
        if total_size > settings.MAXIMUM_MULTIFILE_DOWNLOAD_ZIP_SIZE:
            message = (
                "Total size of files %d is larger than %d. "
                "Try requesting fewer files."
                % (total_size, settings.MAXIMUM_MULTIFILE_DOWNLOAD_ZIP_SIZE)
            )
            logger.warn(message)
            return HttpResponseForbidden(message)

        temp = tempfile.NamedTemporaryFile(suffix=".archive")
        zipName = request.GET.get("zipname", image.getName())

        try:
            zipName = zip_archived_files(images, temp, zipName, buf=settings.CHUNK_SIZE)

            # return the zip or single file
            archivedFile_data = FileWrapper(temp)
            rsp = ConnCleaningHttpResponse(archivedFile_data)
            rsp.conn = conn
            rsp["Content-Length"] = temp.tell()
            rsp["Content-Disposition"] = "attachment; filename=%s" % zipName
            temp.seek(0)
        except Exception:
            temp.close()
            message = "Cannot download file (id:%s)" % (iid)
            logger.error(message, exc_info=True)
            return HttpResponseServerError(message)

    rsp["Content-Type"] = "application/force-download"
    return rsp


@login_required()
@jsonp
def original_file_paths(request, iid, conn=None, **kwargs):
    """
    Get a list of path/name strings for original files associated with the
    image
    """

    image = conn.getObject("Image", iid)
    if image is None:
        raise Http404
    paths = image.getImportedImageFilePaths()
    fileset_id = image.fileset.id.val
    return {
        "repo": paths["server_paths"],
        "client": paths["client_paths"],
        "fileset": {"id": fileset_id},
    }


@login_required()
@jsonp
def get_shape_json(request, roiId, shapeId, conn=None, **kwargs):
    roiId = int(roiId)
    shapeId = int(shapeId)
    shape = conn.getQueryService().findByQuery(
        "select shape from Roi as roi "
        "join roi.shapes as shape "
        "where roi.id = %d and shape.id = %d" % (roiId, shapeId),
        None,
    )
    logger.debug("Shape: %r" % shape)
    if shape is None:
        logger.debug("No such shape: %r" % shapeId)
        raise Http404
    return JsonResponse(shapeMarshal(shape))


@login_required()
@jsonp
def get_rois_json(request, imageId, conn=None, **kwargs):
    """
    Returns json data of the ROIs in the specified image.
    """
    rois = []
    roiService = conn.getRoiService()
    # rois = webfigure_utils.getRoiShapes(roiService, int(imageId))  # gets a
    # whole json list of ROIs
    result = roiService.findByImage(int(imageId), None, conn.SERVICE_OPTS)

    for r in result.rois:
        roi = {}
        roi["id"] = r.getId().getValue()
        # go through all the shapes of the ROI
        shapes = []
        for s in r.copyShapes():
            if s is None:  # seems possible in some situations
                continue
            shapes.append(shapeMarshal(s))
        # sort shapes by Z, then T.
        shapes.sort(key=lambda x: "%03d%03d" % (x.get("theZ", -1), x.get("theT", -1)))
        roi["shapes"] = shapes
        rois.append(roi)

    # sort by ID - same as in measurement tool.
    rois.sort(key=lambda x: x["id"])

    return rois


@login_required()
def histogram_json(request, iid, theC, conn=None, **kwargs):
    """
    Returns a histogram for a single channel as a list of
    256 values as json
    """
    image = conn.getObject("Image", iid)
    if image is None:
        raise Http404

    theZ = int(request.GET.get("theZ", 0))
    theT = int(request.GET.get("theT", 0))
    theC = int(theC)
    binCount = int(request.GET.get("bins", 256))

    if theZ >= image.getSizeZ() or theT >= image.getSizeT() or theC >= image.getSizeC():
        raise Http404

    # TODO: handle projection when supported by OMERO
    try:
        data = image.getHistogram([theC], binCount, theZ=theZ, theT=theT)
        histogram = data[theC]
    except omero.ApiUsageException as ex:
        logger.warn(ex)
        resObj = {"error": ex.message}
        return HttpResponseBadRequest(
            json.dumps(resObj), content_type="application/json"
        )
    return JsonResponse({"data": histogram})


@login_required(isAdmin=True)
@jsonp
def su(request, user, conn=None, **kwargs):
    """
    If current user is admin, switch the session to a new connection owned by
    'user' (puts the new session ID in the request.session)
    Return False if not possible

    @param request:     http request.
    @param user:        Username of new connection owner
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    Can be used to specify the html 'template' for
                        rendering
    @return:            Boolean
    """
    if request.method == "POST":
        conn.setGroupNameForSession("system")
        connector = Connector.from_session(request)
        session = conn.getSessionService().getSession(conn._sessionUuid)
        ttl = session.getTimeToIdle().val
        connector.omero_session_key = conn.suConn(user, ttl=ttl)._sessionUuid
        connector.to_session(request)
        conn.revertGroupForSession()
        conn.close()
        return True
    else:
        context = {
            "url": reverse("webgateway_su", args=[user]),
            "submit": "Do you want to su to %s" % user,
        }
        template = "webgateway/base/includes/post_form.html"
        return render(request, template, context)


def _annotations(request, objtype, objid, conn=None, **kwargs):
    warnings.warn("Deprecated. Use _bulk_file_annotations()", DeprecationWarning)
    return _bulk_file_annotations(request, objtype, objid, conn, **kwargs)


def _bulk_file_annotations(request, objtype, objid, conn=None, **kwargs):
    """
    Retrieve Bulk FileAnnotations for object specified by object type and
    identifier optionally traversing object model graph.
    Returns dictionary containing annotations in NSBULKANNOTATIONS namespace
    if successful, otherwise returns error information.
    If the graph has multiple parents, we return annotations from all parents.

    Example:  /annotations/Plate/1/
              retrieves annotations for plate with identifier 1
    Example:  /annotations/Plate.wells/1/
              retrieves annotations for plate that contains well with
              identifier 1
    Example:  /annotations/Screen.plateLinks.child.wells/22/
              retrieves annotations for screen that contains plate with
              well with identifier 22

    @param request:     http request.
    @param objtype:     Type of target object, or type of target object
                        followed by a slash-separated list of properties to
                        resolve
    @param objid:       Identifier of target object, or identifier of object
                        reached by resolving given properties
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    unused
    @return:            A dictionary with key 'error' with an error message or
                        with key 'data' containing an array of dictionaries
                        with keys 'id' and 'file' of the retrieved annotations
    """
    q = conn.getQueryService()
    # If more than one objtype is specified, use all in query to
    # traverse object model graph
    # Example: /annotations/Plate/wells/1/
    #          retrieves annotations from Plate that contains Well 1
    objtype = objtype.split(".")

    params = omero.sys.ParametersI()
    params.addId(objid)
    params.addString("ns", NSBULKANNOTATIONS)
    params.addString("mt", "OMERO.tables")

    query = "select obj0 from %s obj0\n" % objtype[0]
    for i, t in enumerate(objtype[1:]):
        query += "join fetch obj%d.%s obj%d\n" % (i, t, i + 1)
    query += """
        left outer join fetch obj0.annotationLinks links
        left outer join fetch links.child as f
        left outer join fetch links.parent
        left outer join fetch f.file
        join fetch links.details.owner
        join fetch links.details.creationEvent
        where obj%d.id=:id and
        (f.ns=:ns or f.file.mimetype=:mt)""" % (
        len(objtype) - 1
    )

    ctx = conn.createServiceOptsDict()
    ctx.setOmeroGroup("-1")

    try:
        objs = q.findAllByQuery(query, params, ctx)
    except omero.QueryException:
        return dict(error="%s cannot be queried" % objtype, query=query)

    data = []
    # Process all annotations from all objects...
    links = [link for obj in objs for link in obj.copyAnnotationLinks()]
    for link in links:
        annotation = link.child
        if not isinstance(annotation, omero.model.FileAnnotation):
            continue
        owner = annotation.details.owner
        ownerName = "%s %s" % (unwrap(owner.firstName), unwrap(owner.lastName))
        addedBy = link.details.owner
        addedByName = "%s %s" % (unwrap(addedBy.firstName), unwrap(addedBy.lastName))
        data.append(
            dict(
                id=annotation.id.val,
                name=unwrap(annotation.file.name),
                file=annotation.file.id.val,
                ns=unwrap(annotation.ns),
                parentType=objtype[0],
                parentId=link.parent.id.val,
                owner=ownerName,
                addedBy=addedByName,
                addedOn=unwrap(link.details.creationEvent._time),
            )
        )
    return dict(data=data)


annotations = login_required()(jsonp(_bulk_file_annotations))


def perform_table_query(
    conn,
    fileid,
    query,
    col_names,
    offset=0,
    limit=None,
    lazy=False,
    check_max_rows=True,
):
    ctx = conn.createServiceOptsDict()
    ctx.setOmeroGroup("-1")

    r = conn.getSharedResources()
    t = r.openTable(omero.model.OriginalFileI(fileid), ctx)
    if not t:
        return dict(error="Table %s not found" % fileid)

    try:
        cols = t.getHeaders()
        col_indices = range(len(cols))
        if col_names:
            enumerated_columns = (
                [(i, j) for (i, j) in enumerate(cols) if j.name in col_names]
                if col_names
                else [(i, j) for (i, j) in enumerate(cols)]
            )
            cols = []
            col_indices = []
            for col_name in col_names:
                for i, j in enumerated_columns:
                    if col_name == j.name:
                        col_indices.append(i)
                        cols.append(j)
                        break

        column_names = [col.name for col in cols]
        rows = t.getNumberOfRows()

        range_start = offset
        range_size = limit if limit is not None else rows
        range_end = min(rows, range_start + range_size)

        if query == "*":
            hits = range(range_start, range_end)
            totalCount = rows
        else:
            match = re.match(r"^(\w+)-(\d+)", query)
            if match:
                c_name = match.group(1)
                if c_name in ("Image", "Roi", "Plate", "Well"):
                    # older tables may have column named e.g. 'image'
                    if c_name not in column_names and c_name.lower() in column_names:
                        c_name = c_name.lower()
                query = "(%s==%s)" % (c_name, match.group(2))
            try:
                logger.info(query)
                hits = t.getWhereList(query, None, 0, rows, 1)
                totalCount = len(hits)
                # paginate the hits
                hits = hits[range_start:range_end]
            except Exception:
                return dict(error="Error executing query: %s" % query)

        if check_max_rows:
            if len(hits) > settings.MAX_TABLE_DOWNLOAD_ROWS:
                error = (
                    "Trying to download %s rows exceeds configured"
                    " omero.web.max_table_download_rows of %s"
                ) % (len(hits), settings.MAX_TABLE_DOWNLOAD_ROWS)
                return {"error": error, "status": 404}

        def row_generator(table, h):
            # hits are all consecutive rows - can load them in batches
            idx = 0
            batch = settings.MAX_TABLE_DOWNLOAD_ROWS
            while idx < len(h):
                batch = min(batch, len(h) - idx)
                res = table.slice(col_indices, h[idx : idx + batch])
                idx += batch
                # yield a list of rows
                yield [
                    [col.values[row] for col in res.columns]
                    for row in range(0, len(res.rowNumbers))
                ]

        row_gen = row_generator(t, hits)

        rsp_data = {
            "data": {
                "column_types": [col.__class__.__name__ for col in cols],
                "columns": column_names,
            },
            "meta": {
                "rowCount": rows,
                "totalCount": totalCount,
                "limit": limit,
                "offset": offset,
            },
        }

        if not lazy:
            row_data = []
            # Use the generator to add all rows in batches
            for rows in list(row_gen):
                row_data.extend(rows)
            rsp_data["data"]["rows"] = row_data
        else:
            rsp_data["data"]["lazy_rows"] = row_gen
            rsp_data["table"] = t

        return rsp_data
    finally:
        if not lazy:
            t.close()


def _table_query(request, fileid, conn=None, query=None, lazy=False, **kwargs):
    """
    Query a table specified by fileid
    Returns a dictionary with query result if successful, error information
    otherwise

    @param request:     http request; querystring must contain key 'query'
                        with query to be executed, or '*' to retrieve all rows.
                        If query is in the format word-number, e.g. "Well-7",
                        if will be run as (word==number), e.g. "(Well==7)".
                        This is supported to allow more readable query strings.
    @param fileid:      Numeric identifier of file containing the table
    @param query:       The table query. If None, use request.GET.get('query')
                        E.g. '*' to return all rows.
                        If in the form 'colname-1', query will be (colname==1)
    @param lazy:        If True, instead of returning a 'rows' list,
                        'lazy_rows' will be a generator.
                        Each gen.next() will return a list of row data
                        AND 'table' returned MUST be closed.
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    offset, limit
    @return:            A dictionary with key 'error' with an error message
                        or with key 'data' containing a dictionary with keys
                        'columns' (an array of column names) and 'rows'
                        (an array of rows, each an array of values)
    """
    if query is None:
        query = request.GET.get("query")
    if not query:
        return dict(error="Must specify query parameter, use * to retrieve all")
    col_names = request.GET.getlist("col_names")

    offset = kwargs.get("offset", 0)
    limit = kwargs.get("limit", None)
    if not offset:
        offset = int(request.GET.get("offset", 0))
    if not limit:
        limit = (
            int(request.GET.get("limit"))
            if request.GET.get("limit") is not None
            else None
        )
    return perform_table_query(
        conn, fileid, query, col_names, offset=offset, limit=limit, lazy=lazy
    )


table_query = login_required()(jsonp(_table_query))


def _table_metadata(request, fileid, conn=None, query=None, lazy=False, **kwargs):
    ctx = conn.createServiceOptsDict()
    ctx.setOmeroGroup("-1")

    r = conn.getSharedResources()
    t = r.openTable(omero.model.OriginalFileI(fileid), ctx)
    if not t:
        return dict(error="Table %s not found" % fileid)

    try:
        cols = t.getHeaders()
        rows = t.getNumberOfRows()
        allmeta = t.getAllMetadata()

        user_metadata = {}
        for k in allmeta:
            if allmeta[k].__class__ == omero.rtypes.RStringI:
                try:
                    val = json.loads(allmeta[k].val)
                    user_metadata[k] = val
                except json.decoder.JSONDecodeError:
                    user_metadata[k] = allmeta[k].val
            else:
                user_metadata[k] = allmeta[k].val
        rsp_data = {
            "columns": [
                {
                    "name": col.name,
                    "description": col.description,
                    "type": col.__class__.__name__,
                }
                for col in cols
            ],
            "totalCount": rows,
            "user_metadata": user_metadata,
        }
        return rsp_data
    finally:
        if not lazy:
            t.close()


table_metadata = login_required()(jsonp(_table_metadata))


@login_required()
@jsonp
def obj_id_bitmask(request, fileid, conn=None, query=None, **kwargs):
    """
    Get an ID bitmask representing which ids match the given query
    Returns a http response where the content is a 0-indexed array of
    big-endian bit-ordered bytes representing the selected ids.
    E.g. if your query returns IDs 1,2,7, 11, and 12, you will
    get back 0110000100011000, or [97, 24]. The response will be the
    smallest number of bytes necessary to represent all IDs and will
    be padded with 0s to the end of the byte.

    @param request:     http request; querystring must contain key 'query'
                        with query to be executed, or '*' to retrieve all rows.
                        If query is in the format word-number, e.g. "Well-7",
                        if will be run as (word==number), e.g. "(Well==7)".
                        This is supported to allow more readable query strings.
                        querystring may optionally specify 'col_name' which is
                        the ID column to use to create the mask. By default
                        'object' is used.
    @param fileid:      Numeric identifier of file containing the table
    @param query:       The table query. If None, use request.GET.get('query')
                        E.g. '*' to return all rows.
                        If in the form 'colname-1', query will be (colname==1)
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    offset, limit
    @return:            A dictionary with key 'error' with an error message
                        or with an array of bytes as described above
    """

    col_name = request.GET.get("col_name", "object")
    if query is None:
        query = request.GET.get("query")
    if not query:
        return dict(error="Must specify query parameter, use * to retrieve all")

    offset = kwargs.get("offset", 0)
    limit = kwargs.get("limit", None)
    if not offset:
        offset = int(request.GET.get("offset", 0))
    if not limit:
        limit = (
            int(request.GET.get("limit"))
            if request.GET.get("limit") is not None
            else None
        )

    ctx = conn.createServiceOptsDict()
    ctx.setOmeroGroup("-1")
    sr = conn.getSharedResources()
    table = sr.openTable(omero.model.OriginalFileI(fileid, False), ctx)
    if not table:
        return {"error": "Table %s not found" % fileid}
    try:
        column_names = [column.name for column in table.getHeaders()]
        if col_name not in column_names:
            # Previous implementations used perform_table_query() which
            # defaults to returning all columns if the requested column name
            # is unknown.  We would have then packed the first column.  We
            # mimic that here by only querying for the first column.
            #
            # FIXME: This is really weird behaviour, especially with this
            # endpoint defaulting to using the "object" column, and likely
            # deserves to be refactored and deprecated or changed
            # accordingly.
            col_name = column_names[0]
        row_numbers = table.getWhereList(query, None, 0, 0, 1)
        # If there are no matches for the query, don't call table.slice()
        if len(row_numbers) == 0:
            return HttpResponse(
                numpy.packbits(numpy.array([0], dtype="int64")).tobytes(),
                content_type="application/octet-stream",
            )
        (column,) = table.slice([column_names.index(col_name)], row_numbers).columns
        try:
            return HttpResponse(
                column_to_packed_bits(column), content_type="application/octet-stream"
            )
        except ValueError:
            logger.error("ValueError when getting obj_id_bitmask")
            return {"error": "Specified column has invalid type"}
    except Exception:
        logger.error("Error when getting obj_id_bitmask", exc_info=True)
        return {"error", "Unexpected error getting obj_id_bitmask"}
    finally:
        table.close()


def column_to_packed_bits(column):
    """
    Convert a column of integer values (strings will be coerced) to a bit mask
    where each value present will be set to 1.
    """
    if len(column.values) > 0 and isinstance(column.values[0], float):
        raise ValueError("Cannot have ID of float")
    # Coerce strings to int64 if required.  If we have values > 2**63 they
    # wouldn't work anyway so signed is okay here.  Note that the
    # implementation does get weird if the indexes are negative values.
    indexes = numpy.array(column.values, dtype="int64")
    bits = numpy.zeros(int(indexes.max() + 1), dtype="uint8")
    bits[indexes] = 1
    return numpy.packbits(bits, bitorder="big").tobytes()


@login_required()
@jsonp
def object_table_query(request, objtype, objid, conn=None, **kwargs):
    """
    Query bulk annotations table attached to an object specified by
    object type and identifier, optionally traversing object model graph.
    Returns a dictionary with query result if successful, error information
    otherwise

    Example:  /table/Plate/1/query/?query=*
              queries bulk annotations table for plate with identifier 1
    Example:  /table/Plate.wells/1/query/?query=*
              queries bulk annotations table for plate that contains well with
              identifier 1
    Example:  /table/Screen.plateLinks.child.wells/22/query/?query=Well-22
              queries bulk annotations table for screen that contains plate
              with well with identifier 22

    @param request:     http request.
    @param objtype:     Type of target object, or type of target object
                        followed by a slash-separated list of properties to
                        resolve
    @param objid:       Identifier of target object, or identifier of object
                        reached by resolving given properties
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    unused
    @return:            A dictionary with key 'error' with an error message
                        or with key 'data' containing a dictionary with keys
                        'columns' (an array of column names) and 'rows'
                        (an array of rows, each an array of values)
    """
    a = _bulk_file_annotations(request, objtype, objid, conn, **kwargs)
    if "error" in a:
        return a

    if len(a["data"]) < 1:
        return dict(error="Could not retrieve bulk annotations table")

    # multiple bulk annotations files could be attached, use the most recent
    # one (= the one with the highest identifier)
    fileId = 0
    ann = None
    annList = sorted(a["data"], key=lambda x: x["file"], reverse=True)
    tableData = None
    for annotation in annList:
        tableData = _table_query(request, annotation["file"], conn, **kwargs)
        if "error" not in tableData:
            ann = annotation
            fileId = annotation["file"]
            break
    if ann is None:
        return dict(
            error=tableData.get(
                "error", "Could not retrieve matching bulk annotation table"
            )
        )
    tableData["id"] = fileId
    tableData["annId"] = ann["id"]
    tableData["owner"] = ann["owner"]
    tableData["addedBy"] = ann["addedBy"]
    tableData["parentType"] = ann["parentType"]
    tableData["parentId"] = ann["parentId"]
    tableData["addedOn"] = ann["addedOn"]
    return tableData


class LoginView(View):
    """Webgateway Login - Subclassed by WebclientLoginView."""

    form_class = LoginForm
    useragent = "OMERO.webapi"

    @method_decorator(sensitive_post_parameters("password", "csrfmiddlewaretoken"))
    def dispatch(self, *args, **kwargs):
        """Wrap other methods to add decorators."""
        return super(LoginView, self).dispatch(*args, **kwargs)

    def get(self, request, api_version=None):
        """Simply return a message to say GET not supported."""
        return JsonResponse(
            {"message": ("POST only with username, password, " "server and csrftoken")},
            status=405,
        )

    def handle_logged_in(self, request, conn, connector):
        """Return a response for successful login."""
        c = conn.getEventContext()
        ctx = {}
        for a in [
            "sessionId",
            "sessionUuid",
            "userId",
            "userName",
            "groupId",
            "groupName",
            "isAdmin",
            "eventId",
            "eventType",
            "memberOfGroups",
            "leaderOfGroups",
        ]:
            if hasattr(c, a):
                ctx[a] = getattr(c, a)
        return JsonResponse({"success": True, "eventContext": ctx})

    def handle_not_logged_in(self, request, error=None, form=None):
        """
        Return a response for failed login.

        Reason for failure may be due to server 'error' or because
        of form validation errors.

        @param request:     http request
        @param error:       Error message
        @param form:        Instance of Login Form, populated with data
        """
        if error is None and form is not None:
            # If no error from server, maybe form wasn't valid
            formErrors = []
            for field in form:
                for e in field.errors:
                    formErrors.append("%s: %s" % (field.label, e))
            error = " ".join(formErrors)
        elif error is None:
            # Just in case no error or invalid form is given
            error = "Login failed. Reason unknown."
        return JsonResponse({"message": error}, status=403)

    def post(self, request, api_version=None):
        """
        Here we handle the main login logic, creating a connection to OMERO.

        and store that on the request.session OR handling login failures
        """
        error = None
        form = self.form_class(request.POST.copy())
        userip = get_client_ip(request)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            server_id = form.cleaned_data["server"]
            is_secure = settings.SECURE

            connector = Connector(server_id, is_secure)

            # TODO: version check should be done on the low level, see #5983
            compatible = True
            if settings.CHECK_VERSION:
                compatible = connector.check_version(self.useragent)
            if (
                server_id is not None
                and username is not None
                and password is not None
                and compatible
            ):
                conn = connector.create_connection(
                    self.useragent, username, password, userip=userip
                )
                if conn is not None:
                    try:
                        connector.to_session(request)
                        # UpgradeCheck URL should be loaded from the server or
                        # loaded omero.web.upgrades.url allows to customize web
                        # only
                        try:
                            upgrades_url = settings.UPGRADES_URL
                        except Exception:
                            upgrades_url = conn.getUpgradesUrl()
                        upgradeCheck(url=upgrades_url)
                        return self.handle_logged_in(request, conn, connector)
                    finally:
                        conn.close(hard=False)
            # Once here, we are not logged in...
            # Need correct error message
            if not connector.is_server_up(self.useragent):
                error = "Server is not responding," " please contact administrator."
            elif not settings.CHECK_VERSION:
                error = (
                    "Connection not available, please check your"
                    " credentials and version compatibility."
                )
            else:
                if not compatible:
                    error = (
                        "Client version does not match server,"
                        " please contact administrator."
                    )
                else:
                    error = settings.LOGIN_INCORRECT_CREDENTIALS_TEXT
        elif "connector" in request.session and (
            len(form.data) == 0
            or ("csrfmiddlewaretoken" in form.data and len(form.data) == 1)
        ):
            # If we appear to already be logged in and the form we've been
            # provided is empty repeat the "logged in" behaviour so a user
            # can get their event context.  A form with length 1 is considered
            # empty as a valid CSRF token is required to even get into this
            # method.  The CSRF token may also have been provided via HTTP
            # header in which case the form length will be 0.
            connector = Connector.from_session(request)
            # Do not allow retrieval of the event context of the public user
            if not connector.is_public:
                conn = connector.join_connection(self.useragent, userip)
                # Connection is None if it could not be successfully joined
                # and any omero.client objects will have had close() called
                # on them.
                if conn is not None:
                    try:
                        return self.handle_logged_in(request, conn, connector)
                    except Exception:
                        pass
                    finally:
                        conn.close(hard=False)
        return self.handle_not_logged_in(request, error, form)


@login_required()
@jsonp
def get_image_rdefs_json(request, img_id=None, conn=None, **kwargs):
    """
    Retrieves all rendering definitions for a given image (id).

    Example:  /get_image_rdefs_json/1
              Returns all rdefs for image with id 1

    @param request:     http request.
    @param img_id:      the id of the image in question
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    unused
    @return:            A dictionary with key 'rdefs' in the success case,
                        one with key 'error' if something went wrong
    """
    try:
        img = conn.getObject("Image", img_id)

        if img is None:
            return {"error": "No image with id " + str(img_id)}

        return {"rdefs": img.getAllRenderingDefs()}
    except Exception:
        logger.debug(traceback.format_exc())
        return {"error": "Failed to retrieve rdefs"}


@login_required()
@jsonp
def table_get_where_list(request, fileid, conn=None, **kwargs):
    """
    Retrieves matching row numbers for a table query

    Example: /webgateway/table/123/rows/?query=object<100&start=50

    Query arguments:
    query: table query in PyTables syntax
    start: row number to start searching

    Uses MAX_TABLE_SLICE_SIZE to determine how many rows will be searched.

    @param request:     http request.
    @param fileid:      the id of the table
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    unused
    @return:            A dictionary with keys 'rows' and 'meta' in the success case,
                        one with key 'error' if something went wrong.
                        'rows' is an array of matching row numbers.
                        'meta' includes:
                            - rowCount: total number of rows in table
                            - columnCount: total number of columns in table
                            - start: row on which search was started
                            - end: row on which search ended (exclusive), can be used
                              for follow-up query as new start value if end<rowCount
                            - maxCells: maximum number of cells that can be requested
                              in one request
                            - partialCount: number of matching rows returned in this
                              response. Important: if start>0 and/or end<rowCount,
                              this may not be the total number of matching rows in the
                              table!
    """

    query = request.GET.get("query")
    if not query:
        return {"error": "Must specify query"}
    try:
        start = int(request.GET.get("start"))
    except (ValueError, TypeError):
        start = 0
    ctx = conn.createServiceOptsDict()
    ctx.setOmeroGroup("-1")
    resources = conn.getSharedResources()
    table = resources.openTable(omero.model.OriginalFileI(fileid), ctx)
    if not table:
        return {"error": "Table %s not found" % fileid}
    try:
        row_count = table.getNumberOfRows()
        column_count = len(table.getHeaders())
        end = min(row_count, start + settings.MAX_TABLE_SLICE_SIZE)
        logger.info(f"Query '{query}' from rows {start} to {end}")
        hits = table.getWhereList(query, None, start, end, 1) if start < end else []
        return {
            "rows": hits,
            "meta": {
                "partialCount": len(hits),
                "rowCount": row_count,
                "columnCount": column_count,
                "start": start,
                "end": end,
                "maxCells": settings.MAX_TABLE_SLICE_SIZE,
            },
        }
    except Exception:
        return {"error": "Error executing query: %s" % query}
    finally:
        table.close()


@login_required()
@jsonp
def table_slice(request, fileid, conn=None, **kwargs):
    """
    Performs a table slice

    Example: /webgateway/table/123/slice/?rows=1,2,5-10&columns=0,3-4

    Query arguments:
    rows: row numbers to retrieve in comma-separated list,
          hyphen-separated ranges allowed
    columns: column numbers to retrieve in comma-separated list,
             hyphen-separated ranges allowed

    At most MAX_TABLE_SLICE_SIZE data points (number of rows * number of columns) can
    be retrieved, if more are requested, an error is returned.

    @param request:     http request.
    @param fileid:      the id of the table
    @param conn:        L{omero.gateway.BlitzGateway}
    @param **kwargs:    unused
    @return:            A dictionary with keys 'columns' and 'meta' in the success
                        case, one with key 'error' if something went wrong.
                        'columns' is an array of column data arrays
                        'meta' includes:
                            - rowCount: total number of rows in table
                            - columns: names of columns in same order as data arrays
                            - columnCount: total number of columns in table
                            - maxCells: maximum number of cells that can be requested
                              in one request
    """

    def parse(item):
        try:
            yield int(item)
        except ValueError:
            start, end = item.split("-")
            if start > end:
                raise ValueError("Invalid range")
            yield from range(int(start), int(end) + 1)

    def limit_generator(generator, max_items):
        for counter, item in enumerate(generator):
            if counter >= max_items:
                raise ValueError("Too many items")
            yield item

    source = request.POST if request.method == "POST" else request.GET
    try:
        # Limit number of items to avoid problems when given massive ranges
        rows = list(
            limit_generator(
                (row for item in source.get("rows").split(",") for row in parse(item)),
                settings.MAX_TABLE_SLICE_SIZE,
            )
        )
        columns = list(
            limit_generator(
                (
                    column
                    for item in source.get("columns").split(",")
                    for column in parse(item)
                ),
                settings.MAX_TABLE_SLICE_SIZE / len(rows),
            )
        )
    except (ValueError, AttributeError) as error:
        return {
            "error": f"Need comma-separated list of rows and columns ({str(error)})"
        }
    ctx = conn.createServiceOptsDict()
    ctx.setOmeroGroup("-1")
    resources = conn.getSharedResources()
    table = resources.openTable(omero.model.OriginalFileI(fileid), ctx)
    if not table:
        return {"error": "Table %s not found" % fileid}
    column_count = len(table.getHeaders())
    row_count = table.getNumberOfRows()
    if not all(0 <= column < column_count for column in columns):
        return {"error": "Columns out of range"}
    if not all(0 <= row < row_count for row in rows):
        return {"error": "Rows out of range"}
    try:
        columns = table.slice(columns, rows).columns
        return {
            "columns": [column.values for column in columns],
            "meta": {
                "columns": [column.name for column in columns],
                "rowCount": row_count,
                "columnCount": column_count,
                "maxCells": settings.MAX_TABLE_SLICE_SIZE,
            },
        }
    except Exception as error:
        logger.exception(
            "Error slicing table %s with %d columns and %d rows"
            % (fileid, len(columns), len(rows))
        )
        return {"error": f"Error slicing table ({str(error)})"}
    finally:
        table.close()
