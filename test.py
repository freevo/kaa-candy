import os
import sys
import kaa

sys.path.append('src')

@kaa.coroutine()
def main():
    import widgets
    import stage

    stage = stage.Stage((800,600), 'candy')
    w = widgets.Rectangle((40, 40))
    stage.add(w)
    yield kaa.NotFinished
    w.x = 2
    yield kaa.NotFinished
    yield kaa.NotFinished

main()
kaa.main.run()
print 'shutdown'
