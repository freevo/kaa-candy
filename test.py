import os
import gc
import sys
import kaa
import kaa.candy2

xml = '''
<candyxml geometry="800x600">
    <group name="g1" x="10" y="10" width="600" height="580">
        <rectangle width="50%" height="100" color="0xffff00" radius="50"
           border_size="5" border_color="0xffffff"/>
        <label y="120" font="Vera:24" color="0x00ff00">Test</label>
        <text y="150" font="Vera:24" color="0xff0000" align="center">
Multiline
Text
        </text>
        <label y="180" font="Vera:24" color="0x00ff00" width="200" height="100">
            <properties xalign="center" yalign="center"/>
            center
        </label>
        <group name="g2" x="10" y="300">
            <rectangle x="10" width="100%" y="10" height="100%" color="0x08cccccc" radius="50"
               border_size="5" border_color="0xffffff">
                <properties passive="True"/>
            </rectangle>
            <rectangle x="20" width="100" height="100" color="0xffff00" radius="50"
               border_size="5" border_color="0xffffff"/>
        </group>
        <group name="g3">
            <properties xalign="center" yalign="bottom"/>
            <rectangle x="10" width="100%" y="10" height="100%" color="0x05cccccc">
                <properties passive="True"/>
            </rectangle>
            <label x="20" y="20" color="0x000000" font="Vera:24">highlight</label>
        </group>
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
