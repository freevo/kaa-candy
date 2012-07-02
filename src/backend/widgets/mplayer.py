# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# mplayer.py - mplayer video widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# The widget does not use kaa.popcorn because gstreamer using
# kaa.candy and mplayer are too different to add support to
# kaa.popcorn without rewriting too much. Furthermore, kaa.popcorn
# seems to have a raise condition I cannot find and is too complex;
# much is not needed.
#
# Some parts of this code is copied from kaa.popcorn.
#
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2012 Dirk Meyer
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

__all__ = [ 'Mplayer' ]

# Python imports
import os
import sys
import re
import subprocess

# Clutter GI bindings
from gi.repository import Clutter as clutter

# kaa.display for mplayer to draw to
import kaa.display

import widget

# mplayer progress status line parser
RE_STATUS = re.compile(r'(?:V:\s*([\d.]+)|A:\s*([\d.]+)\s\W)(?:.*\s([\d.]+x))?')

class ArgumentList(list):
    """
    Argument list.
    """
    def __init__(self, args=()):
        if isinstance(args, basestring):
            args = args.split(' ')
        list.__init__(self, args)

    def __getslice__(self, i, j):
        return ArgumentList(list.__getslice__(self, i, j))

    def extend(self, arg):
        try:
            list.extend(self, arg.split(' '))
        except AttributeError:
            list.extend(self, arg)


SEEK_RELATIVE = 'SEEK_RELATIVE'
SEEK_ABSOLUTE = 'SEEK_ABSOLUTE'
SEEK_PERCENTAGE = 'SEEK_PERCENTAGE'

class Mplayer(widget.Widget):
    """
    Mplayer video widget.
    """

    child = None

    def create(self):
        """
        Create the clutter object
        """
        self.cmd = ArgumentList('mplayer')
        self.obj = clutter.Texture()
        self.obj.hide()

    #
    # control callbacks from the main process
    #

    @kaa.threaded(kaa.MAINTHREAD)
    def do_play(self):
        """
        Start playback
        """
        try:
            self.window = kaa.display.X11Window(size=(self.width,self.height))
            self.window.set_fullscreen()
            self.window.set_cursor_visible(False)
            self.window.signals['key_press_event'].connect_weak(self.event_key)
            self.window.is_hidden = True
            cmd = self.cmd[:]
            cmd.extend('-v -osdlevel 0 -slave -nolirc -nojoystick')
            # video playback
            cmd.extend('-fs -wid %s' % str(self.window.id))
            # vpdau
            if self.audio_only:
                cmd.extend('-vo null')
            else:
                if self.config['mplayer.vdpau']:
                    cmd.extend('-vo vdpau,xv,x11 -vc ffvc1vdpau,ffh264vdpau,')
            # passthrough
            if self.config['mplayer.passthrough']:
                cmd.extend('-ac hwac3,hwdts,')
            self.child = kaa.Process(cmd + [ self.url ])
            self.child.delimiter = ['\r', '\n']
            self.child.stop_command = 'quit\nquit\n'
            self.child.signals['exited'].connect_weak_once(self.event_exit)
            self.child.signals['readline'].connect_weak(self.event_stdout)
            # lower the window before showing it. If kaa.candy is also
            # fullscreen the window is hidden until the playback
            # starts
            self.window.lower()
            self.window.show()
            self.child.start()
        except Exception, e:
            # We should use the logging module somehow and get the
            # logging info to the main process.
            print 'mplayer:', e

    @kaa.threaded(kaa.MAINTHREAD)
    def do_stop(self):
        """
        Stop playback
        """
        if not self.window:
            return
        self.child.write('quit\n')

    @kaa.threaded(kaa.MAINTHREAD)
    def do_pause(self):
        """
        Pause playback
        """
        self.child.write('pause\n')

    @kaa.threaded(kaa.MAINTHREAD)
    def do_resume(self):
        """
        Resume playback
        """
        self.child.write('pause\n')

    def do_seek(self, value, type):
        """
        Seek to the given position
        """
        if self.child:
            s = [SEEK_RELATIVE, SEEK_PERCENTAGE, SEEK_ABSOLUTE]
            return self.child.write('seek %s %s\n' % (value, s.index(type)))
        # Playback is not started. We can use the seek command line
        # argument.
        if type in (SEEK_RELATIVE, SEEK_ABSOLUTE):
            # sorry, we do not support more here
            self.cmd.extend('-ss %s' % value)

    def do_set_audio(self, idx):
        """
        Set the audio stream
        """
        if self.child:
            return self.child.write('switch_audio %s\n' % idx)
        self.cmd.extend('-aid %s' % idx)

    def do_set_subtitle(self, idx):
        """
        Set the subtitle stream (-1 == none)
        """
        if self.child:
            return self.child.write('sub_select %s\n' % idx)
        if idx >= 0:
            return self.cmd.extend('-sid %s' % idx)

    #
    # events from mplayer
    #

    def event_key(self, key):
        """
        Key press in the player window
        """
        self.server.send_event('key_press', key)

    def event_stdout(self, line):
        """
        Stdout line from the running mplayer process
        """
        if line.startswith('V:') or line.startswith('A:'):
            m = RE_STATUS.search(line)
            if not m:
                return
            if self.window.is_hidden:
                self.window.raise_()
                self.window.is_hidden = False
            self.server.send_event('widget_call', self.wid, 'progress', float(m.groups()[0]))

    def event_exit(self, code):
        """
        The player has stopped
        """
        if not self.window:
            return
        self.child.signals['readline'].disconnect(self.event_stdout)
        self.window.signals['key_press_event'].disconnect(self.event_key)
        self.window.hide()
        self.server.send_event('widget_call', self.wid, 'finished')
        self.window = None
        self.child = None
