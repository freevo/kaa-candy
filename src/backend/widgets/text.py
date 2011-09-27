# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - text widget
# -----------------------------------------------------------------------------
# $Id:$
#
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
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

__all__ = [ 'Text' ]

import clutter
import pango

import widget

class Text(widget.Widget):

    def create(self):
        """
        Create the clutter object
        """
        self.obj = clutter.Text()
        self.obj.show()

    def update(self, modified):
        """
        Render the widget
        """
        super(Text, self).update(modified)
        if 'align' in modified and self.align:
            self.obj.set_line_alignment(str(self.align))
        self.obj.set_line_wrap(True)
        self.obj.set_line_wrap_mode(pango.WRAP_WORD_CHAR)
        self.obj.set_use_markup(True)
        self.obj.set_font_name("%s %spx" % (self.font.name, self.font.size))
        self.obj.set_color(clutter.Color(*self.color))
        self.obj.set_ellipsize(pango.ELLIPSIZE_END)
        self.obj.set_text(self.text)
