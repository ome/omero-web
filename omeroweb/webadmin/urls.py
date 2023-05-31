#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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
# Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>, 2008.
#
# Version: 1.0
#

from django.urls import re_path

from omeroweb.webadmin import views
from omeroweb.webclient.views import WebclientLoginView

# url patterns
urlpatterns = [
    re_path(r"^$", views.index, name="waindex"),
    re_path(r"^login/$", WebclientLoginView.as_view(), name="walogin"),
    re_path(r"^logout/$", views.logout, name="walogout"),
    re_path(
        r"^forgottenpassword/$", views.forgotten_password, name="waforgottenpassword"
    ),
    re_path(r"^experimenters/$", views.experimenters, name="waexperimenters"),
    re_path(
        r"^experimenter/(?P<action>[a-z]+)/(?:(?P<eid>[0-9]+)/)?$",
        views.manage_experimenter,
        name="wamanageexperimenterid",
    ),
    re_path(
        r"^change_password/(?P<eid>[0-9]+)/$",
        views.manage_password,
        name="wamanagechangepasswordid",
    ),
    re_path(r"^groups/$", views.groups, name="wagroups"),
    re_path(
        r"^group/(?P<action>(new|create|edit|save))/" "(?:(?P<gid>[0-9]+)/)?$",
        views.manage_group,
        name="wamanagegroupid",
    ),
    re_path(
        r"^group_owner/(?P<action>(edit|save))/(?P<gid>[0-9]+)/$",
        views.manage_group_owner,
        name="wamanagegroupownerid",
    ),
    re_path(
        r"^myaccount/(?:(?P<action>[a-z]+)/)?$", views.my_account, name="wamyaccount"
    ),
    re_path(r"^stats/$", views.stats, name="wastats"),
    re_path(
        r"^drivespace_json/groups/$",
        views.drivespace_json,
        {"query": "groups"},
        name="waloaddrivespace_groups",
    ),
    re_path(
        r"^drivespace_json/users/$",
        views.drivespace_json,
        {"query": "users"},
        name="waloaddrivespace_users",
    ),
    re_path(
        r"^drivespace_json/group/(?P<groupId>[0-9]+)/$",
        views.drivespace_json,
        name="waloaddrivespace_group",
    ),
    re_path(
        r"^drivespace_json/user/(?P<userId>[0-9]+)/$",
        views.drivespace_json,
        name="waloaddrivespace_user",
    ),
    # NB: eid is not used and is optional in URL.
    # Left in place to avoid breaking change.
    re_path(
        r"^change_avatar/(?:(?P<eid>[0-9]+)/)?(?:(?P<action>[a-z]+)/)?$",
        views.manage_avatar,
        name="wamanageavatar",
    ),
    re_path(r"^myphoto/$", views.myphoto, name="wamyphoto"),
    re_path(r"^email/$", views.email, name="waemail"),
]
