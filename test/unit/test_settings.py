#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Copyright (c) 2008 University of Dundee.
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
Simple integration tests to ensure that the settings are working correctly.
"""

from omeroweb.connector import Server


# Test model
class TestServerModel(object):
    def test_constructor(self):
        Server.reset()
        # Create object with alias
        Server(host="example.com", port=4064, server="ome")

        # Create object without alias
        Server(host="example2.com", port=4065)

        # without any params
        try:
            Server()
        except TypeError as te:
            found = str(te)
            error_message = (
                "__new__() missing 2 required positional arguments:"
                " 'host' and 'port'"
            )
            assert found.endswith(error_message)

    def test_get_and_find(self):
        Server.reset()

        SERVER_LIST = [
            ["example1.com", 4064, "omero1"],
            ["example2.com", 4064, "omero2"],
            ["example3.com", 4064],
            ["example4.com", 4064],
        ]
        for s in SERVER_LIST:
            server = (len(s) > 2) and s[2] or None
            Server(host=s[0], port=s[1], server=server)

        s1 = Server.get(1)
        assert s1.host == "example1.com"
        assert s1.port == 4064
        assert s1.server == "omero1"

        s2 = Server.find("example2.com")[0]
        assert s2.host == "example2.com"
        assert s2.port == 4064
        assert s2.server == "omero2"

    def test_load_server_list(self):
        Server.reset()

        SERVER_LIST = [
            ["example1.com", 4064, "omero1"],
            ["example2.com", 4064, "omero2"],
            ["example3.com", 4064],
            ["example4.com", 4064],
        ]
        for s in SERVER_LIST:
            server = (len(s) > 2) and s[2] or None
            Server(host=s[0], port=s[1], server=server)
        Server.freeze()

        try:
            Server(host="example5.com", port=4064)
        except TypeError as te:
            assert str(te) == "No more instances allowed"

        Server(host="example1.com", port=4064)
