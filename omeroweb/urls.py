#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#
# Copyright (c) 2008-2014 University of Dundee.
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

import logging
import importlib.util
from django.conf import settings
from django.apps import AppConfig
from django.conf.urls import include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect

from django.urls import re_path, reverse
from django.utils.functional import lazy
from django.views.generic import RedirectView
from django.views.decorators.cache import never_cache
from omeroweb.webclient import views as webclient_views

logger = logging.getLogger(__name__)

# error handler
handler404 = "omeroweb.feedback.views.handler404"
handler500 = "omeroweb.feedback.views.handler500"

reverse_lazy = lazy(reverse, str)


def redirect_urlpatterns():
    """
    Helper function to return a URL pattern for index page http://host/.
    """
    if settings.INDEX_TEMPLATE is None:
        return [
            re_path(
                r"^$",
                never_cache(
                    RedirectView.as_view(url=reverse_lazy("webindex"), permanent=True)
                ),
                name="index",
            )
        ]
    else:
        return [
            re_path(
                r"^$",
                never_cache(
                    RedirectView.as_view(
                        url=reverse_lazy("webindex_custom"), permanent=True
                    )
                ),
                name="index",
            ),
        ]


# url patterns

urlpatterns = []

for app in settings.ADDITIONAL_APPS:
    if isinstance(app, AppConfig):
        app_config = app
    else:
        app_config = AppConfig.create(app)
    label = app_config.label

    # Depending on how we added the app to INSTALLED_APPS in settings.py,
    # include the urls the same way
    if "omeroweb.%s" % app in settings.INSTALLED_APPS:
        urlmodule = "omeroweb.%s.urls" % app
    else:
        urlmodule = "%s.urls" % app

    # Try to import module.urls.py if it exists (not for corsheaders etc)
    urls_found = importlib.util.find_spec(urlmodule)
    if urls_found is not None:
        try:
            __import__(urlmodule)
            # https://stackoverflow.com/questions/7580220/django-urls-how-to-map-root-to-app
            if label == settings.OMEROWEB_ROOT_APPLICATION:
                regex = r"^"
            else:
                regex = "^%s/" % label
            urlpatterns.append(re_path(regex, include(urlmodule)))
        except ImportError:
            print(
                """Failed to import %s
Please check if the app is installed and the versions of the app and
OMERO.web are compatible
            """
                % urlmodule
            )
            raise
    else:
        logger.debug("Module not found: %s" % urlmodule)

urlpatterns += [
    re_path(
        r"^favicon\.ico$",
        lambda request: redirect("%s%s" % (settings.STATIC_URL, settings.FAVICON_URL)),
        name="favicon",
    ),
    re_path(r"^webgateway/", include("omeroweb.webgateway.urls")),
    re_path(r"^webadmin/", include("omeroweb.webadmin.urls")),
    re_path(r"^webclient/", include("omeroweb.webclient.urls")),
    re_path(r"^url/", include("omeroweb.webredirect.urls")),
    re_path(r"^feedback/", include("omeroweb.feedback.urls")),
    re_path(r"^api/", include("omeroweb.api.urls")),
    re_path(r"^index/$", webclient_views.custom_index, name="webindex_custom"),
]

urlpatterns += redirect_urlpatterns()


if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
