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
Simple unit tests for the webgateway common_filters.
"""

from datetime import datetime, timedelta
from omeroweb.webgateway.templatetags.common_filters import ago


class TestFilters(object):
    """
    Tests various filter methods
    """

    def test_ago(self):
        now = datetime.now()
        assert ago(now - timedelta(seconds=15)) == "less than a minute"
        assert ago(now - timedelta(minutes=15)) == "15 minutes"
        assert ago(now - timedelta(minutes=75)) == "1 hour"
        assert ago(now - timedelta(hours=15)) == "15 hours"
        assert ago(now - timedelta(hours=36)) == "1 day"
        assert ago(now - timedelta(days=1)) == "1 day"
        assert ago(now - timedelta(days=5, hours=12)) == "5 days"
        assert ago(now - timedelta(days=24)) == "24 days"
        assert ago(now - timedelta(days=29)) == "29 days"
        assert ago(now - timedelta(weeks=2)) == "14 days"
        assert ago(now - timedelta(weeks=5)) == "1 month"
        assert ago(now - timedelta(weeks=260)) == "4 years"
        assert ago(now + timedelta(seconds=15)) == "Future times not supported"
