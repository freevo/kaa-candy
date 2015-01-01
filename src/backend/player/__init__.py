# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# widgets - backend files for the widgets
# -----------------------------------------------------------------------------
# This directory contains the video and audio player widgets. This
# module should not be accessed directly and exposes all its players
# to candy.players
#
# -----------------------------------------------------------------------------
# kaa-candy - Third generation Canvas System using Clutter as backend
# Copyright (C) 2011-2012 Dirk Meyer, Jason Tackaberry
#
# Based on various previous attempts to create a canvas system for
# Freevo by Dirk Meyer and Jason Tackaberry.  Please see the file
# AUTHORS for a complete list of authors.
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

__all__ = []

import logging
import kaa.utils
import candy

# get logging object
log = logging.getLogger('candy')

for name, module in kaa.utils.get_plugins(location=__file__).items():
    if not hasattr(module, 'Player'):
        if str(module) == 'KAA_CANDY_SKIP':
            # player we expect to fail for now
            log.info('disable player %s' % name)
            continue
        # This should never happen and is for developing inside
        # kaa.candy only. Still, we should use the logging module
        # somehow and get the logging info to the main process.
        log.error('disable player %s: %s' % (name, module))
        continue
    candy.player[name] = getattr(module, 'Player')

def init(server):
    """
    Called after import
    """
    server.send_event('player', candy.player.keys())
