# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# setup.py - Setup script for kaa.candy
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2008-2011 Dirk Meyer, Jason Tackaberry
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
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
import sys
import os
import sys
import stat
try:
    # kaa base imports
    from kaa.distribution.core import Extension, setup
    import kaa.utils
except ImportError:
    print 'kaa.base not installed'
    sys.exit(1)

print 'checking for gobject-introspection ...',
try:
    import gi.repository
except ImportError:
    print 'not found'
    sys.exit(1)
print 'ok'

# version checks
def check_version(name, major_version, minor_version=0):
    print 'checking for gir %s %s.%s ...' % (name, major_version, minor_version),
    try:
        exec('from gi.repository import %s as module' % name)
    except ImportError:
        print 'not found'
        sys.exit(1)
    if hasattr(module, 'MAJOR_VERSION'):
        if module.MAJOR_VERSION != major_version:
            print 'failed'
            print 'wrong major version: %s.%s' % (module.MAJOR_VERSION, module.MINOR_VERSION)
            sys.exit(1)
        if module.MINOR_VERSION < minor_version:
            print 'failed'
            print 'wrong minor version: %s.%s' % (module.MAJOR_VERSION, module.MINOR_VERSION)
            sys.exit(1)
    else:
        if int(module._version.split('.')[0]) != major_version:
            print 'failed'
            print 'wrong major version: %s' % module._version
            sys.exit(1)
    print 'ok'

check_version('GObject', 2)
check_version('Gst', 1)
check_version('Clutter', 1, 6)
check_version('ClutterGst', 2)

if len(sys.argv) == 2 and sys.argv[1] == 'clean':
    for file in ('build', 'dist', 'src/version.py', 'MANIFEST',
                 'src/backend/gen_libcandy.c'):
        if os.path.isdir(file):
            print 'removing %s' % file
            os.system('rm -rf %s' % file)
        if os.path.isfile(file):
            print 'removing %s' % file
            os.unlink(file)
    sys.exit(0)

# now trigger the python magic
setup(
    module = 'candy',
    version = '0.0.2',
    license = 'GPL',
    summary = 'Fourth generation Canvas System using Clutter as backend',
    namespace_packages = ['kaa']
)
