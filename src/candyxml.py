# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# candyxml.py - Parser to parse XML into widget Templates
# -----------------------------------------------------------------------------
# $Id$
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

__all__ = [ 'parse', 'register', 'get_class' ]

# python imports
import os
import logging
import xml.sax
import imp

# kaa.candy imports
from core import Color, Font

# get logging object
log = logging.getLogger('kaa.candy')


class ElementDict(dict):

    def __getattr__(self, attr):
        return self.get(attr)


class Element(object):
    """
    XML node element.
    """
    def __init__(self, node, parent, attrs):
        self.content = ''
        self.node = node
        # note: circular reference
        self._parent = parent
        self._attrs = {}
        for key, value in attrs.items():
            if key in ('x', 'xpadding', 'y', 'ypadding'):
                value = int(value)
            elif key == 'width' and not value.endswith('%'):
                x1 = int(attrs.get('x', 0))
                x2 = int(attrs.get('x', 0)) + int(value)
                value = x2 - x1
            elif key == 'height' and not value.endswith('%'):
                y1 = int(attrs.get('y', 0))
                y2 = int(attrs.get('y', 0)) + int(value)
                value = y2 - y1
            elif key in ('radius', 'size', 'spacing'):
                value = int(value)
            elif key.find('color') != -1:
                value = Color(value)
            elif key.find('font') != -1:
                value = Font(value)
                value.size = int(value.size)
            self._attrs[str(key).replace('-', '_')] = value
        self._children = []

    @property
    def candyxml(self):
        root = self._parent
        while getattr(root, '_parent', None) is not None:
            root = root._parent
        return root

    def __iter__(self):
        """
        Iterate over the list of children.
        """
        return self._children[:].__iter__()

    def __getitem__(self, pos):
        """
        Return nth child.
        """
        return self._children[pos]

    def __getattr__(self, attr):
        """
        Return attribute or child with the given name.
        """
        if attr == 'pos':
            return [ self._attrs.get('x', 0), self._attrs.get('y', 0) ]
        if attr == 'size':
            return self.width, self.height
        value = self._attrs.get(attr)
        if value is not None:
            return value
        for child in self._children:
            if child.node == attr:
                return child
        if attr in ('width', 'height'):
            # Set width or height to None. All widgets except the grid will
            # accept such values. The real value will be inserted later
            # based on the parent settings
            return None
        return None

    def xmlcreate(element):
        """
        Create a template or object from XML.
        """
        parser = _parser.get(element.node)
        if parser is None:
            raise RuntimeError('no parser for %s' % element.node)
        parser = parser.candyxml_parse(element)
        if parser is None:
            raise RuntimeError('no parser for %s:%s' % (element.node, element.style))
        return getattr(parser, '__template__', parser).candyxml_create(element)

    def get_children(self, node=None):
        """
        Return all children with the given node name
        """
        if node is None:
            return self._children[:]
        return [ c for c in self._children if c.node == node ]

    def attributes(self):
        """
        Get key/value list of all attributes.,
        """
        return self._attrs.items()

    def remove(self, child):
        """
        Remove the given child element.
        """
        self._children.remove(child)


class CandyXML(xml.sax.ContentHandler):
    """
    candyxml parser.
    """
    def __init__(self, data, elements=None, path=None):
        xml.sax.ContentHandler.__init__(self)
        self._elements = elements or ElementDict()
        # Internal stuff
        self._root = None
        self._current = None
        self._stack = []
        self._names = []
        self._path = path
        self.scripts = {}
        self._parser = xml.sax.make_parser()
        self._parser.setContentHandler(self)
        if data.find('<') >= 0:
            # data is xml data
            self._parser.feed(data)
        else:
            # data is filename
            self._parser.parse(data)

    def get_elements(self):
        """
        Return root attributes and parsed elements
        """
        if self._root[0] == '__candyxml_simple__':
            # fake candyxml tree, only one element
            return self._elements.values()[0].values()[0]
        return dict(self._root[1]), self._elements

    def startElement(self, name, attrs):
        """
        SAX Callback.
        """
        if self._root is None:
            self._root = name, attrs
            if not name in _parser.keys():
                # must be a parent tag like cnadyxml around
                # everything. This means we may have more than one
                # widget in this xml stream.
                return
            # create fake root
            self._root = '__candyxml_simple__', {}
        if name == 'alias' and len(self._stack) == 0:
            self._names.append(attrs['name'])
            return
        element = Element(name, self._current or self, attrs)
        if self._current is not None:
            self._stack.append(self._current)
            self._current._children.append(element)
        else:
            self._names.append(attrs.get('name'))
        self._current = element

    def endElement(self, name):
        """
        SAX Callback.
        """
        if self._current:
            if self._current.content.strip().find('\n') == -1:
                self._current.content = self._current.content.strip()
        if len(self._stack):
            self._current = self._stack.pop()
        elif name == 'alias':
            # alias for high level element, skip
            return
        elif name == 'script':
            if self._path:
                name = os.path.splitext(self._current.filename)[0]
                (file, filename, data) = imp.find_module(name, [ self._path ])
                module = imp.load_module(name, file, filename, data)
                for m in dir(module):
                    if not m.startswith('_'):
                        self.scripts[m] = getattr(module, m)
            self._current = None
            self._names = []
        elif name != self._root[0]:
            screen = self._current.xmlcreate()
            if not self._elements.get(name):
                self._elements[name] = ElementDict()
            for subname in self._names:
                self._elements[name][subname] = screen
            self._current = None
            self._names = []

    def characters(self, c):
        """
        SAX callback
        """
        if self._current:
            self._current.content += c


def parse(data, elements=None):
    """
    Load a candyxml file based on the given screen resolution.
    @param data: filename of the XML file to parse or XML data
    @returns: root element attributes and dict of parsed elements
    """
    if not os.path.isdir(data):
        return CandyXML(data, elements).get_elements()
    attributes = {}
    for f in os.listdir(data):
        if not f.endswith('.xml'):
            continue
        f = os.path.join(data, f)
        try:
            a, elements = CandyXML(f, elements, data).get_elements()
            attributes.update(a)
        except Exception, e:
            log.exception('parse error in %s', f)
    return attributes, elements

class Styles(dict):
    """
    Style dict for candyxml_parse and candyxml_create callbacks
    """
    def candyxml_parse(self, element):
        return self.get(element.style)

#: list of candyxml parser
_parser = {}

def register(cls):
    """
    Register a class
    """
    name = cls.candyxml_name
    parser = _parser
    if not isinstance(cls, Styles):
        if not name in parser:
            parser[name] = Styles()
        parser, name = parser[name], getattr(cls, 'candyxml_style', None)
    if name in parser:
        raise RuntimeError('%s already registered' % name)
    parser[name] = cls

def get_class(name, style):
    """
    Get the class registered to the given name and style
    """
    return _parser.get(name).get(style)
