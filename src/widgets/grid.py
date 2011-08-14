# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# grid.py - Grid Widget
# -----------------------------------------------------------------------------
# $Id:$
#
# -----------------------------------------------------------------------------
# kaa-candy - Third generation Canvas System using Clutter as backend
# Copyright (C) 2008-2011 Dirk Meyer, Jason Tackaberry
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Please see the file AUTHORS for a complete list of authors.
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

__all__ = [ 'Grid' ]

import kaa

import widget
import group

class Grid(group.AbstractGroup):
    candyxml_name = 'grid'
    context_sensitive = True

    HORIZONTAL, VERTICAL =  range(2)

    fixed_size = True

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
        self.items = items
        self.cell_item = cell_item
        self.template = template
        self.spacing = spacing

    def create_grid(self):
        """
        Setup the grid. After this function has has been called no modifications
        to the grid are possible.

        @todo: make it possible to change the layout during runtime
        """
        # do some calculations
        if self.spacing is None:
            # no spacing is given. Get the number of rows and cols
            # and device the remaining space as spacing and border
            self.num_items_x = int(self.width / self.cell_size[0])
            self.num_items_y = int(self.height / self.cell_size[1])
            space_x = self.width / self.num_items_x - self.cell_size[0]
            space_y = self.height / self.num_items_y - self.cell_size[1]
            # size of cells
            self.item_width = self.cell_size[0] + space_x
            self.item_height = self.cell_size[1] + space_y
        else:
            # spacing is given, let's see how much we can fit into here
            space_x, space_y = self.spacing
            # size of cells
            self.item_width = self.cell_size[0] + space_x
            self.item_height = self.cell_size[1] + space_y
            # now that we know the sizes check how much items fit
            self.num_items_x = int(self.width / self.item_width)
            self.num_items_y = int(self.height / self.item_height)
        # we now center the grid by default
        x0 = (self.width - self.num_items_x * self.item_width + space_x) / 2
        y0 = (self.height - self.num_items_y * self.item_height + space_y) / 2
        # list of rendered items
        self.item_widgets = {}
        # group of items
        self.item_group = group.AbstractGroup((x0, y0))
        self.clip = (x0, y0), (self.num_items_x * self.item_width - space_x, self.num_items_y * self.item_height - space_y)
        self.location = (0, 0)
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

    def prepare_sync(self):
        if self.create_grid:
            self.create_grid()
        if not super(Grid, self).prepare_sync():
            return False
        if self.__orientation == Grid.VERTICAL:
            max_x, max_y = self.location
            for y in range(0, max_y + self.num_items_y):
                for x in range(0, max_x + self.num_items_x):
                    item_num = x + y * self.num_items_x
                    if not (x, y) in self.item_widgets:
                        self.create_item(item_num, x, y)
        return super(Grid, self).prepare_sync()

    def context_sync(self):
        self.items = self.__items_provided

    @property
    def items(self):
        return self.__items

    @items.setter
    def items(self, items):
        self.__items_provided = items
        if isinstance(items, (str, unicode)):
            # items is a string, get it from the context
            items = self.context.get(items)
        if self.__items != items:
            if self.__items:
                # we already had a valid list of items.
                self.item_group.clear()
                self.item_widgets = {}
                self.queue_rendering()
            self.__items = items

    @kaa.synchronized()
    def scroll_by(self, (x, y), secs, force=False):
        """
        Scroll by rows and cols cells

        @param x, y: rows and cols to scroll
        @param secs: runtime of the animation
        """
        # This function will force grid creation
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
        self.location = (x, y)
        pos_x = -x * self.item_width + self.clip[0][0]
        pos_y = -y * self.item_height + self.clip[0][1]
        self.item_group.animate('EASE_OUT_CUBIC', secs, 'x', pos_x, 'y', pos_y)
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
        # if subelement width or height are the same of the grid it was
        # copied by candyxml from the parent. Set it to cell width or height
        if subelement.width is element.width:
            subelement.width = int(element.cell_width)
        if subelement.height is element.height:
            subelement.height = int(element.cell_height)
        # return dict
        orientation = Grid.HORIZONTAL
        if element.orientation and element.orientation.lower() == 'vertical':
            orientation = Grid.VERTICAL
        return super(Grid, cls).candyxml_parse(element).update(
            template=subelement.xmlcreate(), items=element.items,
            cell_size=(int(element.cell_width), int(element.cell_height)), cell_item=element.cell_item,
            orientation=orientation)
