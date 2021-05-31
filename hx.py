import time
from machine import Pin

@micropython.native
def toggle(p):
    p.value(1)
    p.value(0)

class HX711:
    def __init__(self, pd_sck=4, dout=5, gain=128):
        self.gain = gain
        self.SCALING_FACTOR = 229
        self.dataPin = Pin(dout, Pin.IN)
        self.pdsckPin = Pin(pd_sck, Pin.OUT, value=0)
        self.powerUp()
        self.value = 0

    def powerUp(self):
        self.pdsckPin.value(0)
        self.powered = True

    def isready(self):
        time.sleep(.001)
        return self.dataPin.value()

    def raw_read(self):
        while not self.isready():
            pass
        time.sleep_us(10)
        my = 0
        for idx in range(24):
            toggle(self.pdsckPin)
            data = self.dataPin.value()
            if not idx:
                neg = data
            else:
                my = ( my << 1) | data
        toggle(self.pdsckPin)
        if neg: my = my - (1<<23)
        return round(my/self.SCALING_FACTOR, 1)
    
