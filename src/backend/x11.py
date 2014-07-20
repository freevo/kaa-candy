# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# x11.py - X11 helper classes
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2014 Dirk Meyer
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# The old ctypes code is broken with newer X server. This is a bad
# hack to make it work again using the xrandr binary. This is not a
# good solution and should be fixed.
#
# Note: Does only work on primary output
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

__all__ = [ 'xrandr' ]

# Python imports
import os
import re

class XrandR(object):

    def __init__(self):
        self.available_rates = []
        for line in os.popen("xrandr").readlines():
            if line.startswith(' ') and line.find("*") > 0:
                for rate in re.findall(' [0-9\.\*]+', line)[1:]:
                    intrate = rate[:rate.find('.')].strip(' +*')
                    if rate.endswith('*'):
                        self._rate = intrate
                    self.available_rates.append(intrate)
                # ignore other outputs
                break

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, rate):
        os.popen("xrandr -r %s" % rate)
        self._rate = rate

xrandr = XrandR()

# Some test code
# print xrandr.available_rates
# print xrandr.rate
# xrandr.rate = "60"
