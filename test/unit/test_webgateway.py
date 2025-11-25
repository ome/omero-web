#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding=utf-8

import os
import numpy
import pytest
from django.http import HttpResponseBadRequest

from omero.columns import LongColumnI
from omeroweb.webgateway.webgateway_tempfile import WebGatewayTempFile
from omeroweb.webgateway import views
import omero.gateway


class TestHelperObjects(object):
    def testColorHolder(self):
        ColorHolder = omero.gateway.ColorHolder
        c1 = ColorHolder()
        assert c1._color == {"red": 0, "green": 0, "blue": 0, "alpha": 255}
        c1 = ColorHolder("blue")
        assert c1.getHtml() == "0000FF"
        assert c1.getCss() == "rgba(0,0,255,1.000)"
        assert c1.getRGB() == (0, 0, 255)
        c1.setRed(0xF0)
        assert c1.getCss() == "rgba(240,0,255,1.000)"
        c1.setGreen(0x0F)
        assert c1.getCss() == "rgba(240,15,255,1.000)"
        c1.setBlue(0)
        assert c1.getCss() == "rgba(240,15,0,1.000)"
        c1.setAlpha(0x7F)
        assert c1.getCss() == "rgba(240,15,0,0.498)"
        c1 = ColorHolder.fromRGBA(50, 100, 200, 300)
        assert c1.getCss() == "rgba(50,100,200,1.000)"

    def testOmeroType(self):
        omero_type = omero.gateway.omero_type
        assert isinstance(omero_type("rstring"), omero.RString)
        assert isinstance(omero_type("rstring"), omero.RString)
        assert isinstance(omero_type(1), omero.RInt)
        # FIXME: python3
        # assert isinstance(omero_type(1), omero.RLong)
        assert isinstance(omero_type(False), omero.RBool)
        assert isinstance(omero_type(True), omero.RBool)
        assert not isinstance(omero_type((1, 2, "a")), omero.RType)

    def testSplitHTMLColor(self):
        splitHTMLColor = omero.gateway.splitHTMLColor
        assert splitHTMLColor("abc") == [0xAA, 0xBB, 0xCC, 0xFF]
        assert splitHTMLColor("abcd") == [0xAA, 0xBB, 0xCC, 0xDD]
        assert splitHTMLColor("abbccd") == [0xAB, 0xBC, 0xCD, 0xFF]
        assert splitHTMLColor("abbccdde") == [0xAB, 0xBC, 0xCD, 0xDE]
        assert splitHTMLColor("#$%&%") is None


def _testCacheFSBlockSize(cache):
    cache.wipe()
    c1 = cache._du()
    cache.set("test/1", "a")
    c2 = cache._du()
    cache.wipe()
    return c1, c2 - c1


class TestWebGatewayCacheTempFile(object):
    @pytest.fixture(autouse=True)
    def setUp(self, request):
        def fin():
            os.system("rm -fr test_cache")

        request.addfinalizer(fin)
        self.tmpfile = WebGatewayTempFile(tdir="test_cache")

    def testFilenameSize(self):
        """
        Make sure slashes, dashes, underscores and other chars don't mess
        things up.
        Also check for filename size limits.
        """
        fname = r'1/2_3!"\'#$%&()=@€£‰¶÷[]≠§±+*~^\,.;:'

        try:
            fpath, rpath, fobj = self.tmpfile.new(fname, key="specialchars")
        except Exception:
            raise
            pytest.fail(
                "WebGatewayTempFile.new not handling special" " characters properly"
            )
        # ext2/3/4 limit is 255 bytes, most others are equal to or larger
        fname = "a" * 384
        try:
            fpath, rpath, fobj = self.tmpfile.new(fname, key="longname")
            fobj.close()
            # is it keeping extensions properly?
            fpath, rpath, fobj = self.tmpfile.new("1" + fname + ".tif", key="longname")
            fobj.close()
            assert fpath[-5:] == "a.tif"
            fpath, rpath, fobj = self.tmpfile.new(
                "2" + fname + ".ome.tiff", key="longname"
            )
            fobj.close()
            assert fpath[-10:] == "a.ome.tiff"
            fpath, rpath, fobj = self.tmpfile.new(
                "3" + fname + "ome.tiff", key="longname"
            )
            fobj.close()
            assert fpath[-6:] == "a.tiff"
            fpath, rpath, fobj = self.tmpfile.new(
                "4" + fname + "somethingverylong.zip", key="longname"
            )
            fobj.close()
            assert fpath[-5:] == "a.zip"
            fpath, rpath, fobj = self.tmpfile.new(
                "5" + fname + ".tif.somethingverylong", key="longname"
            )
            fobj.close()
            assert fpath[-5:] == "aaaaa"
        except Exception:
            pytest.fail(
                "WebGatewayTempFile.new not handling long file names" " properly"
            )


class TestViews(object):
    def testColumnToPackedBits(self):
        column = LongColumnI("test")
        column.values = [1, 2, 7, 11, 12]
        data = numpy.frombuffer(views.column_to_packed_bits(column), dtype="uint8")
        assert data[0] == 97  # 01100001 First, Second and 7th bits
        assert data[1] == 24  # 00011000 11th and 12th bits

    def testGetInvertedEnabled(self):
        mockRequest = {
            "maps": '[{"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}}]'
        }
        inverses = views._get_inverted_enabled(mockRequest, 3)
        assert inverses == [True, False, None]
        mockRequest = {
            "maps": '[{}, {"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": true}}]'
        }
        inverses = views._get_inverted_enabled(mockRequest, 3)
        assert inverses == [False, True, True]
        mockRequest = {
            "maps": '[{}, {"reverse": {"enabled": "true"}},\
            {"inverted": {"enabled": true}}]'
        }
        inverses = views._get_inverted_enabled(mockRequest, 3)
        assert inverses == [False, True, True]

    def testValidateRdefQuery(self):
        class MockRequest(object):
            def __init__(self, data):
                self.GET = data

        def fake_view(request):
            return 1

        wrapped_fake_view = views.validate_rdef_query(fake_view)

        request = MockRequest(
            {
                "m": "c",
                "c": "1|0:255$FF0000,2|0:255$00FF00,3|0:255$0000FF",
                "maps": '[{"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}},\
            {"inverted": {"enabled": "false"}}]',
            }
        )

        assert wrapped_fake_view(request) == 1

        # Unsupported rendering model
        request = MockRequest(
            {
                "m": "x",
                "c": "1|0:255$FF0000,2|0:255$00FF00,3|0:255$0000FF",
                "maps": '[{"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}},\
            {"inverted": {"enabled": "false"}}]',
            }
        )

        assert isinstance(wrapped_fake_view(request), HttpResponseBadRequest) is True

        # Missing rendering model
        request = MockRequest(
            {
                "c": "1|0:255$FF0000,2|0:255$00FF00,3|0:255$0000FF",
                "maps": '[{"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}},\
            {"inverted": {"enabled": "false"}}]',
            }
        )

        assert isinstance(wrapped_fake_view(request), HttpResponseBadRequest) is True

        # Missing window information
        request = MockRequest(
            {
                "m": "c",
                "c": "1|$FF0000,2|0:255$00FF00,3|0:255$0000FF",
                "maps": '[{"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}},\
            {"inverted": {"enabled": "false"}}]',
            }
        )

        assert isinstance(wrapped_fake_view(request), HttpResponseBadRequest) is True

        # Missing color information
        request = MockRequest(
            {
                "m": "c",
                "c": "1|0:255$FF0000,2|0:255,3|0:255$0000FF",
                "maps": '[{"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}},\
            {"inverted": {"enabled": "false"}}]',
            }
        )

        assert isinstance(wrapped_fake_view(request), HttpResponseBadRequest) is True

        # Wrong number of maps
        request = MockRequest(
            {
                "m": "c",
                "c": "1|0:255$FF0000,2|0:255$00FF00,3|0:255$0000FF",
                "maps": '[{"inverted": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}}]',
            }
        )
        assert isinstance(wrapped_fake_view(request), HttpResponseBadRequest) is True
        # Malformed maps JSON
        request = MockRequest(
            {
                "m": "c",
                "c": "1|0:255$FF0000,2|0:255$00FF00,3|0:255$0000FF",
                "maps": '[{"inverted}": {"enabled": "true"}},\
            {"inverted": {"enabled": "false"}}]',
            }
        )
        assert isinstance(wrapped_fake_view(request), HttpResponseBadRequest) is True
