#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2015 University of Dundee & Open Microscopy Environment.
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
Simple unit tests for the "webclient_utils" module.
"""

import pytest
import json

from django.urls import reverse

from omeroweb.utils import reverse_with_params, sort_properties_to_tuple
from omeroweb.webclient.webclient_utils import formatPercentFraction
from omeroweb.webclient.webclient_utils import getDateTime
from omeroweb.connector import Connector


class TestUtil(object):
    """
    Tests various util methods
    """

    def test_format_percent_fraction(self):
        assert formatPercentFraction(1) == "100"
        assert formatPercentFraction(0.805) == "81"
        assert formatPercentFraction(0.2) == "20"
        assert formatPercentFraction(0.01) == "1"
        assert formatPercentFraction(0.005) == "0.5"
        assert formatPercentFraction(0.005) == "0.5"
        assert formatPercentFraction(0.0025) == "0.3"
        assert formatPercentFraction(0.00) == "0.0"

    def test_get_date_time(self):
        """Tests that only a full date-time string is valid"""
        assert getDateTime("2015-12-01 00:00:00") is not None
        assert getDateTime("2015-12-01 23:59:59") is not None
        with pytest.raises(ValueError):
            getDateTime("12345")
        with pytest.raises(ValueError):
            getDateTime("invalid")
        with pytest.raises(ValueError):
            getDateTime("2015-12-01")

    @pytest.mark.parametrize(
        "top_links",
        [
            (
                (
                    '{"viewname": "load_template", "args": ["userdata"],'
                    '"query_string": {"experimenter": -1}}'
                ),
                "/webclient/userdata/?experimenter=-1",
            ),
            (
                '{"viewname": "webindex", "query_string": {"foo": "bar"}}',
                "/webclient/?foo=bar",
            ),
            ('{"viewname": "foo", "args": ["bar"]}', ""),
            ('{"viewname": "foo", "query_string": {"foo": "bar"}}', ""),
        ],
    )
    def test_reverse_with_params_dict(self, top_links):
        top_link = json.loads(top_links[0])
        assert reverse_with_params(**top_link) == top_links[1]

    @pytest.mark.parametrize(
        "top_links",
        [
            ("history", "/webclient/history/"),
            ("webindex", "/webclient/"),
        ],
    )
    def test_reverse_with_params_string(self, top_links):
        top_link = top_links[0]
        assert reverse_with_params(top_link) == reverse(top_link) == top_links[1]

    @pytest.mark.parametrize(
        "top_links",
        [
            ("foo", "str"),
            ("", "str"),
            (None, "NoneType"),
        ],
    )
    def test_bad_reverse_with_params_string(self, top_links):
        kwargs = top_links[0]
        with pytest.raises(TypeError) as excinfo:
            reverse_with_params(**kwargs)
        assert (
            "reverse_with_params() argument after ** must" " be a mapping, not %s"
        ) % top_links[1] in str(excinfo.value)

    @pytest.mark.parametrize(
        "params",
        [
            ([], ()),
            ([{"index": 1, "class": "abc"}], ("abc",)),
            (
                [{"index": 1, "class": "abc"}, {"index": 1, "class": "cde"}],
                ("abc", "cde"),
            ),
            (
                [{"index": 2, "class": "abc"}, {"index": 1, "class": "cde"}],
                ("cde", "abc"),
            ),
            (({"index": 1, "class": "abc"},), ("abc",)),
        ],
    )
    def test_sort_properties_to_tuple(self, params):
        assert sort_properties_to_tuple(params[0]) == params[1]

    def test_sort_properties_to_tuple_custom(self):
        to_sort = [{"foo": 1, "bar": "abc"}]
        sort_by = "foo"
        pick_by = "bar"
        assert sort_properties_to_tuple(to_sort, sort_by, pick_by) == ("abc",)

    @pytest.mark.parametrize(
        "bad_params",
        [
            ([{}], KeyError, "'index'"),
            ([{"foo": 1}], KeyError, "'index'"),
            ([{"index": 1}], KeyError, "'class'"),
        ],
    )
    def test_sort_properties_to_tuple_keyerror(self, bad_params):
        with pytest.raises(bad_params[1]) as excinfo:
            sort_properties_to_tuple(bad_params[0])
        assert bad_params[2] in str(excinfo.value)

    @pytest.mark.parametrize(
        "versions",
        [
            [["4", "4", "4"], ["4", "4", "5"], True],  # major & minor match
            [["5", "4", "4"], ["4", "4", "4"], False],  # major mismatch
            [["5", "3", "4"], ["5", "4", "4"], False],  # minor mismatch
            [["5", "5", "0"], ["5", "4", "4"], False],
            [["5", "5", "0"], ["5", "5", "0"], True],
            [["5", "5", "0"], ["5", "5", "2"], True],
            [["5", "5", "0"], ["5", "6", "0"], True],  # web 5.6+ matches 5.5+
            [["5", "5", "0"], ["5", "8", "0"], True],
            [["5", "5", "0"], ["6", "7", "0"], False],  # major mismatch, >=5
            [["6", "5", "0"], ["6", "7", "0"], False],  # minor mismatch, >=5
        ],
    )
    def test_version_compatible(self, versions):
        server = versions[0]
        client = versions[1]
        compatible = versions[2]
        assert Connector.is_compatible(server, client) == compatible
