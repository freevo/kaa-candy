import os
import sys
import kaa
import kaa.candy2

xml = '''
<candyxml geometry="800x600">
    <group name="g1" x="10" y="10" width="600" height="580">
        <rectangle width="30" height="30"/>
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
    container.x += 100
    yield kaa.NotFinished
    yield kaa.NotFinished

main()
kaa.main.run()
print 'shutdown'
