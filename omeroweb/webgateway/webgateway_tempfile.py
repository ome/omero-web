#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# webgateway/webgateway_tempfile - temporary files for webgateway
#
# Copyright (c) 2008-2024 Glencoe Software, Inc. All rights reserved.
#
# This software is distributed under the terms described by the LICENCE file
# you can find at the root of the distribution bundle, which states you are
# free to use it only for non commercial purposes.
# If the file is missing please request a copy by contacting
# jason@glencoesoftware.com.


import logging
import os
import shutil
import stat
import time
from io import open
from django.conf import settings


TMPROOT = getattr(settings, "WEBGATEWAY_TMPROOT", None)
TMPDIR_TIME = 3600 * 12  # 12 hours


logger = logging.getLogger(__name__)


class AutoLockFile:
    """
    Class extends file to facilitate creation and deletion of lock file.
    """

    def __init__(self, fn, mode):
        """creates a '.lock' file with the specified file name and mode"""
        # FIXME: AutoLockFile previously extended file object
        # super(AutoLockFile, self).__init__(fn, mode)
        self._lock = os.path.join(os.path.dirname(fn), ".lock")
        open(self._lock, "a").close()

    def __del__(self):
        """tries to delete the lock file"""
        try:
            os.remove(self._lock)
        except Exception:
            pass

    def close(self):
        """tries to delete the lock file and close the file"""
        try:
            os.remove(self._lock)
        except Exception:
            pass
        # FIXME: AutoLockFile previously extended file object
        # super(AutoLockFile, self).close()


class WebGatewayTempFile(object):
    """
    Class for handling creation of temporary files
    """

    def __init__(self, tdir=TMPROOT):
        """
        Initialises class, setting the directory to be used for temp files.
        """
        self._dir = tdir
        if tdir and not os.path.exists(self._dir):
            self._createdir()

    def _createdir(self):
        """
        Tries to create the directories required for the temp file base dir
        """
        try:
            os.makedirs(self._dir)
        except OSError:  # pragma: nocover
            raise EnvironmentError(
                "Cache directory '%s' does not exist and"
                " could not be created'" % self._dir
            )

    def _cleanup(self):
        """
        Tries to delete all the temp files that have expired their cache
        timeout.
        """
        now = time.time()
        for f in os.listdir(self._dir):
            try:
                ts = os.path.join(self._dir, f, ".timestamp")
                if os.path.exists(ts):
                    ft = float(open(ts).read()) + TMPDIR_TIME
                else:
                    ft = float(f) + TMPDIR_TIME
                if ft < now:
                    shutil.rmtree(os.path.join(self._dir, f), ignore_errors=True)
            except ValueError:
                continue

    def newdir(self, key=None):
        """
        Creates a new directory using key as the dir name, and adds a
        timestamp file with its creation time. If key is not specified, use a
        unique key based on timestamp.

        @param key:     The new dir name
        @return:        Tuple of (path to new directory, key used)
        """

        if not self._dir:
            return None, None
        self._cleanup()
        stamp = str(time.time())
        if key is None:
            dn = os.path.join(self._dir, stamp)
            while os.path.exists(dn):
                stamp = str(time.time())
                dn = os.path.join(self._dir, stamp)
            key = stamp
        key = key.replace("/", "_")
        try:
            key = key.decode("utf8").encode("ascii", "ignore")
        except AttributeError:
            # python3
            pass
        dn = os.path.join(self._dir, key)
        if not os.path.isdir(dn):
            os.makedirs(dn)
        open(os.path.join(dn, ".timestamp"), "w").write(stamp)
        return dn, key

    def abort(self, fn):
        logger.debug(fn)
        logger.debug(os.path.dirname(fn))
        logger.debug(self._dir)
        if fn.startswith(self._dir):
            shutil.rmtree(os.path.dirname(fn), ignore_errors=True)

    def new(self, name, key=None):
        """
        Creates a new directory if needed, see L{newdir} and checks whether
        this contains a file 'name'. If not, a file lock is created for this
        location and returned.

        @param name:    Name of file we want to create.
        @param key:     The new dir name
        @return:        Tuple of (abs path to new directory, relative path
                        key/name, L{AutoFileLock} or True if exists)
        """

        if not self._dir:
            return None, None, None
        dn, stamp = self.newdir(key)
        name = name.replace("/", "_").replace("#", "_")
        try:
            name = name.decode("utf8").encode("ascii", "ignore")
        except AttributeError:
            # python3
            pass
        if len(name) > 255:
            # Try to be smart about trimming and keep up to two levels of
            # extension (ex: .ome.tiff)
            # We do limit the extension to 16 chars just to keep things sane
            fname, fext = os.path.splitext(name)
            if fext:
                if len(fext) <= 16:
                    fname, fext2 = os.path.splitext(fname)
                    if len(fext + fext2) <= 16:
                        fext = fext2 + fext
                    else:
                        fname += fext2
                else:
                    fname = name
                    fext = ""
            name = fname[: -len(name) + 255] + fext
        fn = os.path.join(dn, name)
        rn = os.path.join(stamp, name)
        lf = os.path.join(dn, ".lock")
        cnt = 30
        fsize = 0
        while os.path.exists(lf) and cnt > 0:
            time.sleep(1)
            t = os.stat(fn)[stat.ST_SIZE]
            if t == fsize:
                cnt -= 1
                logger.debug("countdown %d" % cnt)
            else:
                fsize = t
                cnt = 30
        if cnt == 0:
            return None, None, None
        if os.path.exists(fn):
            return fn, rn, True
        return fn, rn, AutoLockFile(fn, "wb")


webgateway_tempfile = WebGatewayTempFile()
