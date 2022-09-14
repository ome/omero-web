#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


def upgradeCheck(url):
    # upgrade check:
    # -------------
    # On each startup OMERO.web checks for possible server upgrades
    # and logs the upgrade url at the WARNING level. If you would
    # like to disable the checks, please set 'omero.web.upgrades_url`
    # to an empty string.
    #
    # For more information, see
    # https://docs.openmicroscopy.org/latest/omero/sysadmins/UpgradeCheck.html
    #
    try:
        from omero.util.upgrade_check import UpgradeCheck

        if url:
            check = UpgradeCheck("web", url=url)
            check.run()
            if check.isUpgradeNeeded():
                logger.warn(
                    "Upgrade is available. Please visit"
                    " https://downloads.openmicroscopy.org/latest/omero/.\n"
                )
            else:
                logger.debug("Up to date.\n")
    except Exception as x:
        logger.error("Upgrade check error: %s" % x)
