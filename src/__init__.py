# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# __init__.py - kaa.candy main entry point
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011 Dirk Meyer
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Based on various previous attempts to create a canvas system for
# Freevo by Dirk Meyer and Jason Tackaberry.  Please see the file
# AUTHORS for a complete list of authors.
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

# python imports
import sys
import os

if not sys.argv[0].startswith(os.path.dirname(__file__)):
    # only import the submodules from the main application and not
    # from the rendering backend process.
    from core import Context, Color, Font
    from modifier import Modifier, Properties, Eventhandler, Dependency
    from template import is_template, Template
    from widgets import *
    from stage import Stage, Layer

    import candyxml
    import config

    ALIGN_LEFT = Widget.ALIGN_LEFT
    ALIGN_CENTER = Widget.ALIGN_CENTER
    ALIGN_RIGHT = Widget.ALIGN_RIGHT
    ALIGN_TOP = Widget.ALIGN_TOP
    ALIGN_BOTTOM = Widget.ALIGN_BOTTOM
    ALIGN_SHRINK = Widget.ALIGN_SHRINK
