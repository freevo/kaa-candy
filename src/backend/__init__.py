import sys
if 'kaa.candy2' in sys.modules:
    raise RuntimeError('importing the backend is forbidden for the client')
