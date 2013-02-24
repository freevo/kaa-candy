# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# x11.py - X11 helper classes
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2013 Dirk Meyer
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Based on https://github.com/meehow/python-xrandr
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
import time
from ctypes import *

# Load libraries
rr = cdll.LoadLibrary("libXrandr.so.2")
xlib = cdll.LoadLibrary("libX11.so.6")

class Display(object):
    def __init__(self):
        self.display = xlib.XOpenDisplay(os.getenv("DISPLAY"))
        self.screen = xlib.XDefaultScreen(self.display)
        self.root = xlib.XDefaultRootWindow(self.display, self.screen)

class XrandR(object):
    class XRRScreenConfiguration(Structure):
        pass

    def __init__(self):
        self._display = Display()
        gsi = rr.XRRGetScreenInfo
        gsi.restype = POINTER(XrandR.XRRScreenConfiguration)
        self.config = gsi(self._display.display, self._display.root)
        self._id = rr.XRRRootToScreen(self._display.display, self._display.root)
        self._size_index = rr.XRRConfigCurrentConfiguration(self.config, byref(c_ushort()))
        current = c_ushort()
        rr.XRRConfigRotations(self.config, byref(current))
        self._rotation = current.value
        xccr = rr.XRRConfigCurrentRate
        xccr.restype = c_int
        self._rate = xccr(self.config)

    def __del__(self):
        if rr and self.config:
            rr.XRRFreeScreenConfigInfo(self.config)

    def _get_timestamp(self):
        config_timestamp = c_ulong()
        rr.XRRTimes.restpye = c_ulong
        return rr.XRRTimes(self._display.display, self._id, byref(config_timestamp))

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, rate):
        rr.XRRSetScreenConfigAndRate(self._display.display, self.config, self._display.root,
             self._size_index, self._rotation, rate, self._get_timestamp())
        self._rate = rate

    @property
    def available_rates(self):
        rates = []
        nrates = c_int()
        rr.XRRConfigRates.restype = POINTER(c_ushort)
        _rates = rr.XRRConfigRates(self.config, self._size_index, byref(nrates))
        for r in range(nrates.value):
            rates.append(_rates[r])
        return rates

xrandr = XrandR()
