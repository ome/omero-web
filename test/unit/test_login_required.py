#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) Glencoe Software, Inc.
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


from django.conf import settings
from django.test.client import RequestFactory
from omeroweb.webclient.decorators import login_required
import re

rf = RequestFactory()
decorator = login_required()
decorator_allow_public_post = login_required(allowPublicPost=True)


def test_is_valid_public_url_default(monkeypatch):
    assert settings.PUBLIC_ENABLED is False
    assert not hasattr(settings, "PUBLIC_USER")
    assert not hasattr(settings, "PUBLIC_PASSWORD")
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_enabled_no_user(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    assert settings.PUBLIC_ENABLED is True
    assert not hasattr(settings, "PUBLIC_USER")
    assert not hasattr(settings, "PUBLIC_PASSWORD")
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_enabled_no_password(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    assert settings.PUBLIC_ENABLED is True
    assert settings.PUBLIC_USER == "public.user"
    assert not hasattr(settings, "PUBLIC_PASSWORD")
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_nofilter(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_PASSWORD", "password", raising=False)
    assert settings.PUBLIC_ENABLED is True
    assert settings.PUBLIC_USER == "public.user"
    assert settings.PUBLIC_PASSWORD == "password"
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_single_filter(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_PASSWORD", "password", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_URL_FILTER", re.compile("^/api"))
    assert settings.PUBLIC_ENABLED is True
    assert settings.PUBLIC_USER == "public.user"
    assert settings.PUBLIC_PASSWORD == "password"
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_multiple_filter(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_PASSWORD", "password", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_URL_FILTER", re.compile("^/api|webgateway"))
    assert settings.PUBLIC_ENABLED is True
    assert settings.PUBLIC_USER == "public.user"
    assert settings.PUBLIC_PASSWORD == "password"
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_exclude_filter(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_PASSWORD", "password", raising=False)
    monkeypatch.setattr(
        settings,
        "PUBLIC_URL_FILTER",
        re.compile("^/api|webgateway/(?!archived_files|download_as)"),
    )
    assert settings.PUBLIC_ENABLED is True
    assert settings.PUBLIC_USER == "public.user"
    assert settings.PUBLIC_PASSWORD == "password"
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is True
    assert (
        decorator.is_valid_public_url(1, rf.get("/webgateway/archived_files/")) is False
    )
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/download_as/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/render_image/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_getonly(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_PASSWORD", "password", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_URL_FILTER", re.compile("^/api"))
    assert settings.PUBLIC_ENABLED is True
    assert settings.PUBLIC_USER == "public.user"
    assert settings.PUBLIC_PASSWORD == "password"
    assert settings.PUBLIC_GET_ONLY is True
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is True
    assert decorator.is_valid_public_url(1, rf.head("/api/")) is False
    assert decorator.is_valid_public_url(1, rf.post("/api/v0/login")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_public_url_any_method(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_PASSWORD", "password", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_URL_FILTER", re.compile("^/api"))
    monkeypatch.setattr(settings, "PUBLIC_GET_ONLY", False)
    assert settings.PUBLIC_ENABLED is True
    assert settings.PUBLIC_USER == "public.user"
    assert settings.PUBLIC_PASSWORD == "password"
    assert settings.PUBLIC_GET_ONLY is False
    assert decorator.is_valid_public_url(1, rf.get("/api/")) is True
    assert decorator.is_valid_public_url(1, rf.get("/api/v0/")) is True
    assert decorator.is_valid_public_url(1, rf.head("/api/")) is True
    assert decorator.is_valid_public_url(1, rf.post("/api/v0/login")) is True
    assert decorator.is_valid_public_url(1, rf.get("/webgateway/")) is False
    assert decorator.is_valid_public_url(1, rf.get("/webclient/")) is False


def test_is_valid_table_slice_call(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_ENABLED", True)
    monkeypatch.setattr(settings, "PUBLIC_USER", "public.user", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_PASSWORD", "password", raising=False)
    monkeypatch.setattr(settings, "PUBLIC_GET_ONLY", True)
    monkeypatch.setattr(settings, "PUBLIC_URL_FILTER", re.compile("^/api"))
    assert (
        decorator_allow_public_post.is_valid_public_url(
            1, rf.get("/webgateway/table/123/slice")
        )
        is False
    )
    assert (
        decorator_allow_public_post.is_valid_public_url(
            1, rf.post("/webgateway/table/123/slice")
        )
        is False
    )
    monkeypatch.setattr(settings, "PUBLIC_URL_FILTER", re.compile("^/api|webgateway"))
    assert (
        decorator_allow_public_post.is_valid_public_url(
            1, rf.get("/webgateway/table/123/slice")
        )
        is True
    )
    assert (
        decorator_allow_public_post.is_valid_public_url(
            1, rf.post("/webgateway/table/123/slice")
        )
        is True
    )
