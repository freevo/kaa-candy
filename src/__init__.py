import sys
import os

if not sys.argv[0].startswith(os.path.dirname(__file__)):

    from widgets import Widget, Group, Rectangle, Text
    from stage import Stage

    import candyxml
