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

import sys
import platform
import traceback
import logging
from urllib.parse import urlencode

try:
    # python2
    from urllib2 import urlopen, Request, HTTPError, URLError
except ImportError:
    # python3
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
try:
    # python2
    from urlparse import urljoin
except ImportError:
    # python3
    from urllib.parse import urljoin

from omeroweb.version import omeroweb_version as omero_version

from django.conf import settings

logger = logging.getLogger(__name__)


class SendFeedback(object):

    conn = None

    def __init__(self, feedback_url):
        self.url = urljoin(feedback_url, "/qa/initial/")

    def send_feedback(self, error=None, comment=None, email=None, user_agent=""):
        try:
            p = {
                "app_name": settings.FEEDBACK_APP,
                "app_version": omero_version,
                "extra": "",
                "error": (error or ""),
                "email": (email or ""),
                "comment": comment,
            }
            try:
                p["python_classpath"] = sys.path
            except Exception:
                pass
            try:
                p["python_version"] = platform.python_version()
            except Exception:
                pass
            try:
                p["os_name"] = platform.platform()
            except Exception:
                pass
            try:
                p["os_arch"] = platform.machine()
            except Exception:
                pass
            try:
                p["os_version"] = platform.release()
            except Exception:
                pass
            data = urlencode(p)
            data = data.encode()
            headers = {
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain",
                "User-Agent": user_agent,
            }
            request = Request(self.url, data, headers)
            response = None
            try:
                response = urlopen(request)
                if response.code == 200:
                    logger.info(response.read())
                else:
                    logger.error("Feedback server error: %s" % response.reason)
                    raise Exception("Feedback server error: %s" % response.reason)
            except HTTPError as e:
                logger.error(traceback.format_exc())
                raise Exception("Feedback server error: %s" % e.code)
            except URLError as e:
                logger.error(traceback.format_exc())
                raise Exception("Feedback server error: %s" % e.reason)
            finally:
                if response:
                    response.close()
        except Exception as x:
            logger.error(traceback.format_exc())
            raise Exception("Feedback server error: %s" % x)
