import os
import sys
import kaa

sys.path.append('src')

@kaa.coroutine()
def main():
    import widgets
    import stage

    stage = stage.Stage((800,600), 'candy')
    yield kaa.NotFinished

    w = widgets.Rectangle((40, 40))
    stage.add(w)
    stage.sync()
    w.x = 2
    stage.sync()
    stage.sync()
    print 'client running'

main()
kaa.main.run()
print 'shutdown'
