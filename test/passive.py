import kaa
import kaa.candy
        
# create a stage window
stage = kaa.candy.Stage((800,600))

@kaa.coroutine()
def main():
    c1 = kaa.candy.Container()
    r1 = kaa.candy.Rectangle((0,0), (None, '50%'), '0x444444')
    r2 = kaa.candy.Rectangle((0,0), (None, '50%'), '0x888888')
    r3 = kaa.candy.Rectangle((0,0), (100,100), '0xffffff')
    r4 = kaa.candy.Rectangle((200,200), (100,100), '0xffffff')

    c1.passive = True
    c1.parent = stage
    r1.parent = c1
    r2.parent = c1
    r2.passive = True
    
    r3.parent = stage
    r4.parent = stage

    yield kaa.delay(0.3)
    r5 = kaa.candy.Rectangle((300,300), (100,100), '0xffffff')
    r5.parent = stage
    yield kaa.delay(0.3)
    c1.width = 300
    yield kaa.delay(0.3)
    print
    r1.height = '30%'
    print 'done'
    yield kaa.delay(0.3)
    stage.sync()
    
main()
# BUG: we have to sync here because the main loop starts with timer
# and skips the first step call.
stage.sync()
# run the kaa mainloop, it takes some time to load all the images.
kaa.main.run()
