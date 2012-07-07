# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - text widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# FIXME: port this to cairo + pango like label, maybe it will be
# faster. As it is now, it is slow. Maybe draw cairo in another thread???
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011-2012 Dirk Meyer
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

__all__ = [ 'Text' ]

from gi.repository import Clutter as clutter
from gi.repository import Pango as pango

import widget

class Text(widget.Widget):

    def create(self):
        """
        Create the clutter object
        """
        self.obj = clutter.Text.new()
        self.obj.show()

    def update(self, modified):
        """
        Render the widget
        """
        super(Text, self).update(modified)
        if 'align' in modified and self.align:
            self.obj.set_line_alignment(getattr(pango.Alignment, str(self.align).upper()))
        self.obj.set_line_wrap(True)
        self.obj.set_line_wrap_mode(pango.WrapMode.WORD_CHAR)
        self.obj.set_use_markup(True)
        self.obj.set_font_name("%s %spx" % (self.font.name, self.font.size))
        self.obj.set_color(clutter.Color.new(*self.color))
        self.obj.set_ellipsize(pango.EllipsizeMode.END)
        self.obj.set_text(self.text)
