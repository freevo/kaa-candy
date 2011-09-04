import sys
if 'kaa.candy' in sys.modules:
    raise RuntimeError('importing the backend is forbidden for the client')
