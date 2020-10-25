#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2020 University of Dundee & Open Microscopy Environment.
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
"""
Simple unit tests for testing all urls in the application using django reverse, resolve.
"""

from django.urls import reverse, get_resolver, resolve
import django.urls.resolvers as resolvers


url_patterns = list(get_resolver().reverse_dict.keys())
url_pattern_names = [i for i in url_patterns if type(i) == str]


class TestUrls(object):
    """
    Tests all urls within the application
    """

    def test_urls(self):
        for url_name in url_pattern_names:
            patterns = get_resolver().reverse_dict.getlist(url_name)
            kwargs = patterns[0][0][0][1]
            # TODO: Need to test multi-args urls in future PR
            if len(kwargs) == 0:
                kwargs = dict(zip(kwargs, [0] * len(kwargs)))
                result = resolve(reverse(url_name, kwargs=kwargs))
                assert result == resolvers.ResolverMatch
