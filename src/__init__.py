import sys
import os

if not sys.argv[0].startswith(os.path.dirname(__file__)):

    from core import Context, Color, Font, is_template
    from widgets import *
    from stage import Stage

    import candyxml
    import config
