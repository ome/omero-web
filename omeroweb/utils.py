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

from django.utils.http import urlencode
from django.urls import reverse
from django.urls import NoReverseMatch
from past.builtins import basestring


logger = logging.getLogger(__name__)


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
        if not isinstance(qs, basestring):
            qs = urlencode(qs)
        url += "?" + qs
    return url


def sort_properties_to_tuple(input_list, index="index", element="class"):
    return tuple(e[element] for e in sorted(input_list, key=lambda k: k[index]))
