# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# grid.py - grid widget
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

__all__ = [ 'Grid', 'SelectionGrid' ]

# kaa imports
import kaa

# kaa.candy imports
from .. import is_template
from group import AbstractGroup

class Grid(AbstractGroup):
    """
    Grid holding several widgets based on the given items. The grid
    supports scrolling.
    @note: see C{test/flickr.py} for an example
    """
    candyxml_name = 'grid'

    HORIZONTAL, VERTICAL = range(2)

    __items = None

    def __init__(self, pos, size, cell_size, cell_item, items, template,
                 orientation, spacing=None, context=None):
        """
        Simple grid widget to show the items based on the template.

        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget.
        @param cell_size: (width,height) of each cell
        @param cell_item: string how the cell item should be added to the context
        @param items: list of objects or object name in the context
        @param template: child template for each cell
        @param orientation: how to arange the grid: Grid.HORIZONTAL or Grid.VERTICAL
        @param spacing: x,y values of space between two items. If set to None
            the spacing will be calculated based on cell size and widget size
        @param context: the context the widget is created in
        """
        super(Grid, self).__init__(pos, size, context=context)
        # store arguments for later public use
        self.cell_size = cell_size
        # store arguments for later private use
        self.__orientation = orientation
        if isinstance(items, (str, unicode)):
            # items is a string, get it from the context
            items = self.context.get(items)
        self.items = items
        self.cell_item = cell_item
        self.template = template
        self.item_padding = spacing

    def create_grid(self):
        """
        Setup the grid. After this function has has been called no modifications
        to the grid are possible.

        @todo: make it possible to change the layout during runtime
        """
        # do some calculations
        if self.item_padding is None:
            # no spacing is given. Get the number of rows and cols
            # and device the remaining space as spacing and border
            self.num_items_x = int(self.width / self.cell_size[0])
            self.num_items_y = int(self.height / self.cell_size[1])
            padding_x = self.width / self.num_items_x - self.cell_size[0]
            padding_y = self.height / self.num_items_y - self.cell_size[1]
            self.item_padding = padding_x, padding_y
            # size of cells
            self.item_width = self.cell_size[0] + padding_x
            self.item_height = self.cell_size[1] + padding_y
        else:
            # spacing is given, let's see how much we can fit into here
            padding_x, padding_y = self.item_padding
            # size of cells
            self.item_width = self.cell_size[0] + padding_x
            self.item_height = self.cell_size[1] + padding_y
            # now that we know the sizes check how much items fit
            self.num_items_x = int(self.width / self.item_width)
            self.num_items_y = int(self.height / self.item_height)
        # we now center the grid by default
        x0 = (self.width - self.num_items_x * self.item_width + padding_x) / 2
        y0 = (self.height - self.num_items_y * self.item_height + padding_y) / 2
        self.clip = (x0 - padding_x, y0 - padding_y), \
            (self.num_items_x * self.item_width + padding_x, self.num_items_y * self.item_height + padding_y)
        self.location = (0, 0)
        # list of rendered items
        self.item_widgets = {}
        # group of items
        self.item_group = AbstractGroup((x0, y0))
        self.add(self.item_group)
        self.create_grid = None

    def create_item(self, item_num, pos_x, pos_y):
        """
        Render one child
        """
        if item_num < 0 or item_num >= len(self.items):
            self.item_widgets[(pos_x, pos_y)] = None
            return
        # calculate the size where the child should be
        child_x = pos_x * self.item_width
        child_y = pos_y * self.item_height
        context = self.context.copy()
        context[self.cell_item] = self.items[item_num]
        child = self.template(context=context)
        child.x = child_x
        child.y = child_y
        child.width, child.height = self.cell_size
        self.item_group.add(child)
        self.item_widgets[(pos_x, pos_y)] = child
        return child

    def clear(self):
        """
        Clear the grid
        """
        self.item_group.clear()
        self.item_widgets = {}
        self.queue_rendering()

    def sync_prepare(self):
        """
        Prepare widget for the next sync with the backend
        """
        if self.create_grid:
            self.create_grid()
        if not super(Grid, self).sync_prepare():
            return False
        if self.__orientation == Grid.VERTICAL:
            max_x, max_y = self.location
            for y in range(0, max_y + self.num_items_y):
                for x in range(0, max_x + self.num_items_x):
                    item_num = x + y * self.num_items_x
                    if not (x, y) in self.item_widgets:
                        self.create_item(item_num, x, y)
        if self.__orientation == Grid.HORIZONTAL:
            max_x, max_y = self.location
            for x in range(0, max_x + self.num_items_x):
                for y in range(0, max_y + self.num_items_y):
                    item_num = x * self.num_items_y + y
                    if not (x, y) in self.item_widgets:
                        self.create_item(item_num, x, y)
        return super(Grid, self).sync_prepare()

    def sync_context(self):
        """
        Adjust to a new context
        """
        self.items = self.__items_provided

    @property
    def items(self):
        """
        Get list of items
        """
        return self.__items

    @items.setter
    def items(self, items):
        """
        Set list of items
        """
        self.__items_provided = items
        if isinstance(items, (str, unicode)):
            # items is a string, get it from the context
            items = self.context.get(items)
        if self.__items != items:
            if self.__items:
                # we already had a valid list of items.
                self.clear()
            self.__items = items

    @kaa.synchronized()
    def scroll_by(self, (x, y), secs, force=False):
        """
        Scroll by rows and cols cells

        @param x, y: rows and cols to scroll
        @param secs: runtime of the animation
        """
        # This function will force grid creation
        if self.create_grid:
            self.create_grid()
        while not force:
            # check if it possible to go there
            if self.__orientation == Grid.HORIZONTAL:
                num = (self.location[0] + x) * self.num_items_y + \
                      (self.location[1] + y)
            if self.__orientation == Grid.VERTICAL:
                num = (self.location[1] + y) * self.num_items_x + \
                      (self.location[0] + x)
            if num >= 0 and num < len(self.items):
                # there is an item in the upper left corner
                break
            # remove one cell in scroll, start with x and use y if
            # there are no rows to scroll anymore
            if x:
                x -= (x / abs(x))
            else:
                y -= (y / abs(y))
        self.scroll_to((self.location[0] + x, self.location[1] + y), secs)

    @kaa.synchronized()
    def scroll_to(self, (x, y), secs):
        """
        Scroll to row / cell position

        @param x, y: end row and col
        @param secs: runtime of the animation
        """
        if self.create_grid:
            self.create_grid()
        self.location = (x, y)
        pos_x = -x * self.item_width + self.clip[0][0] + self.item_padding[0]
        pos_y = -y * self.item_height + self.clip[0][1] + self.item_padding[1]
        self.item_group.animate('EASE_OUT_CUBIC', secs, x=pos_x, y=pos_y)
        self.queue_rendering()

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
          <grid width='100' height='100' cell-width='30' cell-height='30'
              cell-item='item' items='listing'>
              <image filename='$item.filename'/>
          </grid>
        There is only one child element allowed, if more is needed you need
        to add a container as child with the real children in it.
        """
        subelement = element[0]
        orientation = Grid.HORIZONTAL
        if element.orientation and element.orientation.lower() == 'vertical':
            orientation = Grid.VERTICAL
        if element.cell_width:
            element.cell_width = int(element.cell_width)
        if element.cell_height:
            element.cell_height = int(element.cell_height)
        return super(Grid, cls).candyxml_parse(element).update(
            template=subelement.xmlcreate(), items=element.items,
            cell_size=(element.cell_width, element.cell_height), cell_item=element.cell_item,
            orientation=orientation)



class SelectionGrid(Grid):
    """
    Grid with selection widget.
    @note: see C{test/beacon.py} for an example
    """

    candyxml_style = 'selection'

    def __init__(self, pos, size, cell_size, cell_item, items, template,
                 selection, orientation, spacing=None, context=None):
        """
        Simple grid widget to show the items based on the template.

        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget.
        @param cell_size: (width,height) of each cell
        @param cell_item: string how the cell item should be added to the context
        @param items: list of objects or object name in the context
        @param template: child template for each cell
        @param selection: widget for the selection
        @param orientation: how to arange the grid: Grid.HORIZONTAL or Grid.VERTICAL
        @param spacing: x,y values of space between two items. If set to None
            the spacing will be calculated based on cell size and widget size
        @param context: the context the widget is created in

        """
        super(SelectionGrid, self).__init__(pos, size, cell_size, cell_item, items,
            template, orientation, spacing, context)
        if is_template(selection):
            selection = selection()
        self.selection = selection

    def clear(self):
        """
        Clear the grid
        """
        super(SelectionGrid, self).clear()
        self.item_group.add(self.selection)

    def select(self, (x, y), secs):
        """
        Select a cell.

        @param x, y: cell position to select
        @param secs: runtime of the animation
        """
        if self.create_grid:
            self.create_grid()
        pos_x = x * self.item_width + self.selection.grid_adjust_x
        pos_y = y * self.item_height + self.selection.grid_adjust_y
        self.selection.animate('EASE_OUT_CUBIC', secs, x=pos_x, y=pos_y)
        self.queue_rendering()

    def create_grid(self):
        """
        Setup the grid. After this function has has been called no modifications
        to the grid are possible.

        @todo: make it possible to change the layout during runtime
        """
        super(SelectionGrid, self).create_grid()
        self.item_group.add(self.selection)
        self.selection.grid_adjust_x = self.selection.x = \
            (self.item_width - self.item_padding[0] - self.selection.width) / 2
        self.selection.grid_adjust_y = self.selection.y = \
            (self.item_height - self.item_padding[1] - self.selection.height) / 2

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
          <grid width='100' height='100' cell-width='30' cell-height='30'
              cell-item='item' items='listing'>
              <image filename='$item.filename'/>
              <selection>
                  <rectangle/>
              </selection/>
          </grid>
        There are only the two children element allowed, if more is
        needed you need to add a container as child with the real
        children in it.
        """
        selection = None
        for child in element:
            if child.node == 'selection':
                selection = child[0].xmlcreate()
                element.remove(child)
        return super(SelectionGrid, cls).candyxml_parse(element).update(
            selection=selection)
