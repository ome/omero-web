#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2016 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging

import pytz

from django.utils.http import urlencode
from django.urls import reverse
from django.urls import NoReverseMatch


logger = logging.getLogger(__name__)


def parse_boolean(s):
    s = s.strip().lower()
    if s in ("true", "1", "t"):
        return True
    return False


def identity(x):
    return x


def check_timezone(s):
    """
    Checks that string is a valid time-zone. If not, raise Exception
    """
    pytz.timezone(s)
    return s


def str_slash(s):
    if s is not None:
        s = str(s)
        if s and not s.endswith("/"):
            s += "/"
    return s


class LeaveUnset(Exception):
    pass


def leave_none_unset(s):
    if s is None:
        raise LeaveUnset()
    return s


def leave_none_unset_int(s):
    s = leave_none_unset(s)
    if s is not None:
        return int(s)


def is_ajax(request):
    """
    Replicates the functionality of the Django 3.1 deprecated
    HttpRequest.is_ajax() method for compatibility.
    """
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def reverse_with_params(*args, **kwargs):
    """
    Adds query string to django.urls.reverse
    """

    url = ""
    qs = kwargs.pop("query_string", {})
    try:
        url = reverse(*args, **kwargs)
    except NoReverseMatch:
        return url
    if qs:
        if not isinstance(qs, str):
            qs = urlencode(qs)
        url += "?" + qs
    return url


def sort_properties_to_tuple(input_list, index="index", element="class"):
    return tuple(e[element] for e in sorted(input_list, key=lambda k: k[index]))
