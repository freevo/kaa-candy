import os
import gc
import sys
import kaa
import kaa.candy2

xml = '''
<candyxml geometry="800x600">
    <group name="g1" x="10" y="10" width="600" height="580">
        <rectangle width="30" height="30" color="0xffff00"/>
    </group>
</candyxml>
'''

@kaa.coroutine()
def main():
    stage = kaa.candy2.Stage((400,300), 'candy')
    attr, candy = stage.candyxml(xml)
    if 'geometry' in attr:
        stage.set_content_geometry(attr['geometry'])

    container = candy.group.g1()
    stage.add(container)
    yield kaa.NotFinished
    yield kaa.NotFinished
    container.x += 100
    yield kaa.NotFinished
    #container.parent = None
    yield kaa.NotFinished

def garbage_collect():
    gc.collect()
    for g in gc.garbage:
        print 'Unable to free %s' % g

# Set up garbage collector to be called every 5 seconds
kaa.Timer(garbage_collect).start(1)

main()
kaa.main.run()
print 'shutdown'
