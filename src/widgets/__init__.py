# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# __init__.py - main widget module
# -----------------------------------------------------------------------------
# $Id:$
#
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

__all__ = []

# kaa imports
import kaa.utils

# load all widget files in this directory
for name, module in kaa.utils.get_plugins(location=__file__).items():
    if isinstance(module, Exception):
        raise ImportError('error importing %s: %s' % (name, module))
    for widget in module.__all__:
        __all__.append(widget)
        globals()[widget] = getattr(module, widget)
