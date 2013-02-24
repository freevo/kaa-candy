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
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
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
