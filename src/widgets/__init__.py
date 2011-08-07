__all__ = []

import kaa.utils

for name, module in kaa.utils.get_plugins(location=__file__).items():
    for widget in module.__all__:
        __all__.append(widget)
        globals()[widget] = getattr(module, widget)
