# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# stage.py - Stage class as base for all widgets
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011-2013 Dirk Meyer
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
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

# python imports
import os
import time
import sys
import fcntl
import subprocess
import threading
import logging

# kaa imports
import kaa
import kaa.rpc

# kaa.candy imports
from widgets import Group, Widget, POSSIBLE_PLAYER

import candyxml

# get logging object
log = logging.getLogger('kaa.candy')

# available refresh rates
REFRESH_RATES = []

# turn on internal debug
DEBUG = False

class Layer(Group):
    """
    Group on the stage as parent for widgets added to the stage.
    """

    STATUS_NEW = 'STATUS_NEW'
    STATUS_ACTIVE = 'STATUS_ACTIVE'
    STATUS_DESTROYED = 'STATUS_DESTROYED'

    _state = STATUS_NEW

    def __init__(self, size, widgets=[], context=None):
        super(Layer, self).__init__(size=size, widgets=widgets, context=context)

    def __reset__(self):
        """
        Internal function when the candy backend becomes invalid and
        needs to be restarted.
        """
        super(Layer, self).__reset__()
        self._state = Layer.STATUS_NEW
        Widget._candy_sync_reparent.remove(self)

    @property
    def parent(self):
        return self.stage


class Stage(kaa.Object):
    """
    The stage class is the visible window
    """

    BACKEND_DOWN = 'BACKEND_DOWN'
    BACKEND_INITIALIZING = 'BACKEND_INITIALIZING'
    BACKEND_RUNNING = 'BACKEND_RUNNING'

    __kaasignals__ = {
        'key-press':
            '''
            Emitted when a key in the window is pressed
            '''
    }

    active = True

    def __init__(self, size, name, logfile=''):
        super(Stage, self).__init__()
        self.available_rates = []
        self.name = 'candy-backend-%s' % name
        self.logfile = logfile
        self.size = size
        self.scale = None
        self.backend_state = Stage.BACKEND_DOWN
        # import cache for restart
        self._candy_restart_import = []
        # create the base widget
        self.layer = [ Layer(size=size) ]
        # We need the render pipe, the 'step' signal is not enough. It
        # is not triggered between timer and select and a change done
        # in a timer may get lost.
        self._render_pipe = os.pipe()
        fcntl.fcntl(self._render_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self._render_pipe[1], fcntl.F_SETFL, os.O_NONBLOCK)
        kaa.IOMonitor(self.__sync).register(self._render_pipe[0])
        os.write(self._render_pipe[1], '1')
        self._start_backend()

    @kaa.coroutine()
    def _start_backend(self):
        # spawn the backend process
        args = [ 'python', os.path.dirname(__file__) + '/backend/main.py', self.name, self.logfile ]
        self._candy_dirty = True
        self.server = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)
        retry = 50
        if os.path.exists(kaa.tempfile(self.name)):
            os.unlink(kaa.tempfile(self.name))
        while True:
            try:
                self.ipc = kaa.rpc.connect(self.name)
                yield kaa.inprogress(self.ipc)
                break
            except Exception, e:
                retry -= 1
                if retry == 0:
                    raise e
                time.sleep(0.1)
        self.ipc.signals['closed'].connect_weak_once(self._ipc_disconnect)
        self.ipc.register(self)
        self.backend_state = Stage.BACKEND_INITIALIZING
        self.commands = []
        self.tasks = []
        os.write(self._render_pipe[1], '1')

    def __reset__(self):
        """
        Reset the stage during disconnect
        """
        pass

    @kaa.coroutine()
    def _ipc_disconnect(self):
        """
        Callback when the backend disconnects (crash). This means we
        need to restart it.
        """
        log.error('backend error, restarting')
        self.backend_state = Stage.BACKEND_DOWN
        self.ipc = None
        self.__reset__()
        # remove dead layer
        for layer in self.layer[:]:
            if layer._state == Layer.STATUS_DESTROYED:
                self.layer.remove(layer)
        # start the backend again
        yield self._start_backend()
        # reset widget status
        Widget._candy_sync_new = []
        Widget._candy_sync_reparent = []
        Widget._candy_sync_delete = []
        for widget in Widget._candy_all_widgets:
            widget.__reset__()
        self.__sync()

    def add_layer(self, layer=None, sibling=None):
        """
        Add a new layer and return its id
        """
        if layer is None:
            layer = Layer(size=self.size)
        if self.scale:
            (layer.scale_x, layer.scale_y), (layer.width, layer.height) = self.scale
        if sibling:
            self.layer.insert(self.layer.index(sibling)+1, layer)
            layer.above_sibling(sibling)
        else:
            self.layer.append(layer)
        return len(self.layer) - 1

    def destroy_layer(self, layer):
        """
        Destroy the given layer
        """
        if isinstance(layer, (int, long)):
            layer = self.layer[layer]
        layer._state = Layer.STATUS_DESTROYED

    def hide(self):
        """
        Hide the clutter actors to make it possibile to use the X11
        window for other applications such as a video player.
        """
        for layer in self.layer:
            self.queue_command(layer._candy_id, 'hide', ())

    def show(self):
        """
        Show the clutter actors again after calling hide.
        """
        for layer in self.layer:
            self.queue_command(layer._candy_id, 'show', ())
        self.queue_command(-1, 'ensure_redraw', ())

    def add(self, *widgets, **kwargs):
        """
        Add the given widgets to the stage
        """
        self.layer[kwargs.get('layer', 0)].add(*widgets)

    def remove(self, *widgets, **kwargs):
        """
        Remove the given widgets from the stage
        """
        self.layer[kwargs.get('layer', 0)].remove(*widgets)

    def get_widget(self, name):
        """
        Get child element with the given name. For group children this
        function will search recursive.

        @param name: name of the child
        @returns: widget or None
        """
        for layer in self.layer:
            widget = layer.get_widget(name)
            if widget:
                return widget

    def set_active(self, state):
        """
        Set the Stage active or inactive. If inactive the stage is
        faded out and keys are not handled anymore. Usefull when the
        application is busy somehow.
        """
        if state != self.active:
            self.ipc.rpc('sync', [('active', (state, ))])
            self.active = state
            if state and self.tasks:
                # some queued tasks, rerun sync
                os.write(self._render_pipe[1], '1')

    def queue_rendering(self):
        """
        Queue sync for rendering
        """
        if not self._candy_dirty:
            self._candy_dirty = True
            os.write(self._render_pipe[1], '1')

    def queue_command(self, candy_id, cmd, args):
        """
        Queue sync for a command
        """
        self.commands.append((candy_id, cmd, args))
        self.queue_rendering()

    def __sync(self):
        """
        Sync callback when something changed
        """
        # read the socket to handle the sync
        try:
            os.read(self._render_pipe[0], 1)
        except OSError:
            pass
        if self.backend_state == Stage.BACKEND_DOWN:
            return
        self._candy_dirty = False
        tasks = []
        # check for new imports
        if self.backend_state == Stage.BACKEND_INITIALIZING:
            for i in self._candy_restart_import:
                tasks.append(('import', i))
        while Widget._candy_import:
            module = Widget._candy_import.pop()
            self._candy_restart_import.append(module)
            tasks.append(('import', module))
        if tasks:
            # make sure everything is imported before we need it
            self.ipc.rpc('sync', tasks)
            tasks = []
        # prepare all widgets for the sync
        for layer in self.layer:
            layer.sync_prepare()
        # Create new widgets. The create functions at the backend only
        # create the widgets and not fill it with the actual
        # content. This is done later. Remember the ids of the widget
        # re-arrange the calls later.
        new_widgets = []
        while Widget._candy_sync_new:
            widget = Widget._candy_sync_new.pop(0)
            widget.stage = self
            widget.backend.stage = self
            while widget.backend.queue:
                self.commands.append(widget.backend.queue.pop(0))
            tasks.append(('add', (widget.candy_backend, widget._candy_id)))
            new_widgets.append(widget._candy_id)
        # create stage object if needed
        if self.backend_state == Stage.BACKEND_INITIALIZING:
            self.backend_state = Stage.BACKEND_RUNNING
            tasks.append(('add', ('stage.Stage', -1)))
            tasks.append(('call', (-1, 'init', (self.size, ))))
        # Change parents for the widgets. Remember the needed calls in
        # a seperate variable. We need to reparent before updaing
        # everything here, but maybe do it later on the backend.
        tasks_reparent = []
        while Widget._candy_sync_reparent:
            widget = Widget._candy_sync_reparent.pop(0)
            if widget.parent:
                tasks_reparent.append(('reparent', (widget._candy_id, widget.parent._candy_id, widget._candy_stack)))
            else:
                tasks_reparent.append(('reparent', (widget._candy_id, None, None)))
        # sync all children
        tasks_update = []
        for layer in self.layer[:]:
            if layer._state == Layer.STATUS_NEW:
                tasks.append(('reparent', (layer._candy_id, -1, None)))
                layer._state = Layer.STATUS_ACTIVE
            if layer._state == Layer.STATUS_DESTROYED:
                tasks.append(('reparent', (layer._candy_id, None, None)))
                self.layer.remove(layer)
            else:
                layer.__sync__(tasks_update)
        # Now the tricky part. All create, update and move functions
        # are called in the clutter thread at the backend. If it takes
        # too long, running animations may look strange. But for new
        # objects without parents on the backend we can go back to the
        # clutter main loop from time to time and the user won't see a
        # partial update. Therefore search for new widgets here that
        # gets updated and add the update calls to the tasks list
        # right after the creation. After that add a fake "freeze"
        # call after which going back to the main loop is not allowed
        # anymore. After that freeze add the reparent tasks and all
        # other tasks affecting visible actors.
        for t in tasks_update[:]:
            if t[0] == 'update' and t[1][0] in new_widgets:
                tasks.append(t)
                tasks_update.remove(t)
        self.tasks = self.tasks + tasks + [('freeze', None)] + tasks_reparent + tasks_update
        # add commands for the widgets
        while self.commands:
            self.tasks.append(('call', self.commands.pop(0)))
        while Widget._candy_sync_delete:
            self.tasks.append(('delete', (Widget._candy_sync_delete.pop(0),)))
        # now send everything to the backend
        if self.tasks and self.active:
            if DEBUG:
                print 'sync'
                for t in self.tasks:
                    print '', t
                print
            try:
                if self.ipc:
                    self.ipc.rpc('sync', self.tasks)
                self.tasks = []
            except kaa.rpc.NotConnectedError, e:
                self._ipc_disconnect()

    def set_content_geometry(self, size):
        """
        Set the geometry. This will scale the group in the stage
        """
        if isinstance(size, (str, unicode)):
            size = int(size.split('x')[0]), int(size.split('x')[1])
        self.queue_rendering()
        self.scale = (float(self.size[0]) / size[0], float(self.size[1]) / size[1]), size
        for layer in self.layer:
            (layer.scale_x, layer.scale_y), (layer.width, layer.height) = self.scale

    @kaa.rpc.expose()
    def event_key_press(self, key):
        """
        Callback from the backend on key press
        """
        if self.active:
            self.signals['key-press'].emit(key)

    @kaa.rpc.expose()
    def event_widget_call(self, wid, func, *args, **kwargs):
        """
        Callback for a widget
        """
        for layer in self.layer:
            widget = layer.get_widget_by_id(wid)
            if widget:
                getattr(widget, 'event_%s' % func)(*args, **kwargs)

    @kaa.rpc.expose()
    def event_player(self, player):
        """
        Callback on init to list all possible player
        """
        for p in player:
            POSSIBLE_PLAYER.append(p)

    @kaa.rpc.expose()
    def event_available_rates(self, available_rates):
        """
        Callback on init to list all available refresh rates
        """
        for a in available_rates:
            REFRESH_RATES.append(a)

    def candyxml(self, data):
        """
        Load a candyxml file based on the given screen resolution.

        @param data: filename of the XML file to parse or XML data
        @returns: root element attributes and dict of parsed elements
        """
        attr, templates = candyxml.parse(data)
        if 'geometry' in attr:
            self.set_content_geometry(attr['geometry'])
        return attr, templates
