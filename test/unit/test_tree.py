#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2014 Glencoe Software, Inc.
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

"""
Simple unit tests for the "tree" module.
"""

import pytest

from omero.rtypes import rlong, rstring, rtime, unwrap
from omeroweb.webclient.tree import (
    _marshal_plate_acquisition,
    _marshal_dataset,
    _marshal_date,
    _marshal_image,
    _marshal_image_map,
    _marshal_plate,
    parse_permissions_css,
)


class MockConnection(object):
    def getUserId(self):
        return 1

    def isAdmin(self):
        return False


@pytest.fixture(scope="module")
def mock_conn():
    return MockConnection()


@pytest.fixture(scope="module")
def owner_permissions():
    return {
        "canEdit": True,
        "canAnnotate": True,
        "canLink": True,
        "canDelete": True,
        "canChgrp": True,
    }


@pytest.fixture(scope="module")
def start_time():
    # 2014-05-08 10:37:02 UTC; server timestamps contain ms
    return rtime(1399545422 * 1000)


@pytest.fixture(scope="module")
def end_time():
    # 2014-05-08 10:38:30 UTC; server timestamps contain ms
    return rtime(1399545510 * 1000)


@pytest.fixture(scope="module")
def image_row(owner_permissions):
    return [rlong(1), rstring("name"), rlong(10), owner_permissions, rlong(100)]


@pytest.fixture(scope="module")
def pixels_row():
    return [rlong(1), rlong(2), rlong(3), rlong(4)]


@pytest.fixture()
def image_data(image_row):
    image_id, name, owner_id, permissions, fileset_id = image_row
    return {
        "id": image_id,
        "archived": False,
        "name": name,
        "ownerId": owner_id,
        "image_details_permissions": permissions,
        "filesetId": fileset_id,
    }


@pytest.fixture()
def image_data_with_pixels(image_data, pixels_row):
    sizeX, sizeY, sizeZ, sizeT = pixels_row
    image_data.update(
        {
            "sizeX": sizeX,
            "sizeY": sizeY,
            "sizeZ": sizeZ,
            "sizeT": sizeT,
        }
    )
    return image_data


class TestTree(object):
    """
    Tests to ensure that OMERO.web "tree" infrastructure is working
    correctly.  Order and type of columns in row is:
      * id (rlong)
      * name (rstring)
      * details.owner.id (rlong)
      * details.permissions (dict)
      * startTime (rtime)
      * endTime (rtime)
    """

    def test_marshal_plate_acquisition_no_name_no_start_no_end(
        self, mock_conn, owner_permissions
    ):
        row = [rlong(1), None, rlong(1), owner_permissions, None, None]
        expected = {
            "id": 1,
            "ownerId": 1,
            "name": "Run 1",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp isOwned",
        }

        marshaled = _marshal_plate_acquisition(mock_conn, row)
        assert marshaled == expected

    def test_marshal_plate_acquisition_name_no_start_no_end(
        self, mock_conn, owner_permissions
    ):
        row = [rlong(1), rstring("name"), rlong(1), owner_permissions, None, None]
        expected = {
            "id": 1,
            "ownerId": 1,
            "name": "name",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp isOwned",
        }

        marshaled = _marshal_plate_acquisition(mock_conn, row)
        assert marshaled == expected

    def test_marshal_plate_acquisition_no_name_start_end(
        self, mock_conn, owner_permissions, start_time, end_time
    ):
        row = [rlong(1), None, rlong(1), owner_permissions, start_time, end_time]
        expected = {
            "id": 1,
            "ownerId": 1,
            "name": "2014-05-08 10:37:02 - 2014-05-08 10:38:30",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp isOwned",
        }

        marshaled = _marshal_plate_acquisition(mock_conn, row)
        assert marshaled == expected

    def test_marshal_plate_acquisition_not_owner(self, mock_conn, owner_permissions):
        row = [rlong(1), None, rlong(2), owner_permissions, None, None]
        expected = {
            "id": 1,
            "ownerId": 2,
            "name": "Run 1",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp",
        }

        marshaled = _marshal_plate_acquisition(mock_conn, row)
        assert marshaled == expected

    def test_parse_permissions_css(self, mock_conn):
        restrictions = ("canEdit", "canAnnotate", "canLink", "canDelete", "canChgrp")
        # Iterate through every combination of the restrictions' flags,
        # checking each with and without expected canChgrp
        for i in range(2 ** len(restrictions)):
            expected = []
            permissions_dict = {"perm": "------"}
            for j in range(len(restrictions)):
                if i & 2**j != 0:
                    expected.append(restrictions[j])
                    permissions_dict[restrictions[j]] = True
                else:
                    permissions_dict[restrictions[j]] = False
            expected.sort()
            owner_id = mock_conn.getUserId()
            # Test with different owner_ids, which means canChgrp is False
            received = parse_permissions_css(permissions_dict, owner_id + 1, mock_conn)
            received = list(filter(None, received.split(" ")))
            received.sort()
            assert expected == received
            # Test with matching owner_ids, which means
            # isOwned and canChgrp is True
            expected.append("isOwned")
            expected.sort()
            received = parse_permissions_css(permissions_dict, owner_id, mock_conn)
            received = list(filter(None, received.split(" ")))
            received.sort()
            assert expected == received

    def test_marshal_dataset(self, mock_conn, owner_permissions):
        row = [rlong(1), rstring("name"), rlong(1), owner_permissions, rlong(1)]
        expected = {
            "id": 1,
            "ownerId": 1,
            "name": "name",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp isOwned",
            "childCount": 1,
        }

        marshaled = _marshal_dataset(mock_conn, row)
        assert marshaled == expected

    def test_marshal_dataset_not_owner(self, mock_conn, owner_permissions):
        row = [rlong(1), rstring("name"), rlong(2), owner_permissions, rlong(1)]
        expected = {
            "id": 1,
            "ownerId": 2,
            "name": "name",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp",
            "childCount": 1,
        }

        marshaled = _marshal_dataset(mock_conn, row)
        assert marshaled == expected

    def test_marshal_plate(self, mock_conn, owner_permissions):
        row = [rlong(1), rstring("name"), rlong(1), owner_permissions, 2]
        expected = {
            "id": 1,
            "ownerId": 1,
            "name": "name",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp isOwned",
            "childCount": 2,
        }

        marshaled = _marshal_plate(mock_conn, row)
        assert marshaled == expected

    def test_marshal_plate_not_owner(self, mock_conn, owner_permissions):
        row = [rlong(1), rstring("name"), rlong(2), owner_permissions, 2]
        expected = {
            "id": 1,
            "ownerId": 2,
            "name": "name",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp",
            "childCount": 2,
        }

        marshaled = _marshal_plate(mock_conn, row)
        assert marshaled == expected

    def assert_image(
        self,
        marshaled,
        with_pixels=False,
        with_share=False,
        date=None,
        acqDate=None,
        with_thumbVersion=False,
        is_archived=False,
    ):
        expected = {
            "id": 1,
            "archived": is_archived,
            "ownerId": 10,
            "name": "name",
            "permsCss": "canEdit canAnnotate canLink canDelete canChgrp",
            "filesetId": 100,
        }
        if with_pixels:
            expected.update(
                {
                    "sizeX": 1,
                    "sizeY": 2,
                    "sizeZ": 3,
                    "sizeT": 4,
                }
            )
        if with_share:
            expected.update({"shareId": 1})
        if date:
            # Cannot be static, will include local timezone
            expected.update({"date": _marshal_date(unwrap(date))})
        if acqDate:
            # Cannot be static, will include local timezone
            expected.update({"acqDate": _marshal_date(unwrap(acqDate))})
        if with_thumbVersion:
            expected.update({"thumbVersion": 1})
        assert marshaled == expected

    def test_marshal_image(self, mock_conn, image_row):
        marshaled = _marshal_image(mock_conn, image_row)
        self.assert_image(marshaled)

    def test_marshal_image_with_pixels(self, mock_conn, image_row, pixels_row):
        marshaled = _marshal_image(mock_conn, image_row, pixels_row)
        self.assert_image(marshaled, with_pixels=True)

    def test_marshal_image_with_share(self, mock_conn, image_row):
        marshaled = _marshal_image(mock_conn, image_row, share_id=1)
        self.assert_image(marshaled, with_share=True)

    def test_marshal_image_with_date(self, mock_conn, image_row, end_time):
        marshaled = _marshal_image(mock_conn, image_row, date=end_time)
        self.assert_image(marshaled, date=end_time)

    def test_marshal_image_with_acquisition_date(
        self, mock_conn, image_row, start_time
    ):
        marshaled = _marshal_image(mock_conn, image_row, acqDate=start_time)
        self.assert_image(marshaled, acqDate=start_time)

    def test_marshal_image_with_thumb_version(self, mock_conn, image_row, start_time):
        marshaled = _marshal_image(mock_conn, image_row, thumbVersion=1)
        self.assert_image(marshaled, with_thumbVersion=True)

    def test_marshal_image_map(self, mock_conn, image_data):
        marshaled = _marshal_image_map(mock_conn, image_data)
        self.assert_image(marshaled)

    def test_marshal_image_map_archived(self, mock_conn, image_data):
        image_data["archived"] = True
        marshaled = _marshal_image_map(mock_conn, image_data)
        self.assert_image(marshaled, is_archived=True)

    def test_marshal_image_map_with_pixels(self, mock_conn, image_data_with_pixels):
        marshaled = _marshal_image_map(mock_conn, image_data_with_pixels)
        self.assert_image(marshaled, with_pixels=True)

    def test_marshal_image_map_with_share(self, mock_conn, image_data):
        marshaled = _marshal_image_map(mock_conn, image_data, share_id=1)
        self.assert_image(marshaled, with_share=True)

    def test_marshal_image_map_with_date(self, mock_conn, image_data, end_time):
        marshaled = _marshal_image_map(mock_conn, image_data, date=end_time)
        self.assert_image(marshaled, date=end_time)

    def test_marshal_image_map_with_acquisition_date(
        self, mock_conn, image_data, start_time
    ):
        marshaled = _marshal_image_map(mock_conn, image_data, acqDate=start_time)
        self.assert_image(marshaled, acqDate=start_time)

    def test_marshal_image_map_with_thumb_version(
        self, mock_conn, image_data, start_time
    ):
        marshaled = _marshal_image_map(mock_conn, image_data, thumbVersion=1)
        self.assert_image(marshaled, with_thumbVersion=True)

    # Add a lot of tests
