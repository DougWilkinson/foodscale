from machine import Pin,deepsleep
import time
from hx import HX711
from sensorclass import Sensor
import tm1637
#print(gc.mem_free())


# foodscale using hx711 and segment display tm1637
# Started 4/11/2020
# updated 11/15/2020 to do better weight sampling

tm = tm1637.TM1637(Pin(16),Pin(0))
tm.show('helo',False)
sleeptime = time.ticks_ms() 

bunits = Sensor("bunits", "IN", 4)
units = Sensor("units", "VS", initval=False) # False=grams

def padzero(x):
    xs = str(int(x))
    return('0'*(3-len(xs))+xs)

def display(value,units):
    if time.ticks_ms() - sleep.value > sleep.diff:
        tm.show('off ',False)
        return
    if units:
        tm.write(b'\02',3)
        value = value / 28.35 # ounces if True
    if not units:
        tm.write(b'\04',3)
    if (value >= 1000) or (value <= -0.5):
        tm.show(' err')
        return
    if (value > -0.5) and (value < 0):
        value = 0
    units = False #set colon default off, on if < 100
    if value < 100:
        units = True
        value = value*10
    tm.show(padzero(value), colon=units)

hx = HX711(12,14)
#print(gc.mem_free())

# read hx711 callback
def hxread(x):
    lastsumhx = sum(rawhx.values)
    newhx = hx.raw_read()
    if (newhx < hxmin.value) or (newhx > hxmax.value):
        return
    if abs(newhx - rawhx.value) < 2.5:
        newhx = rawhx.value
    rawhx.values.pop()
    rawhx.values.insert(0,newhx)
    if lastsumhx != sum(rawhx.values):
        rawhx.setvalue(sum(rawhx.values)/len(rawhx.values))

def adjusttoscale(x):
    global sleep
    global scale
    newscale = ((rawhx.value - offset.value) * k.value)
    display(newscale, units.state)
    if abs(scale.value - newscale) > scale.diff:
        scale.setvalue(newscale)
        sleep.value = time.ticks_ms()

# Sensor to poll for readings only

hxmin = Sensor("hxmin", initval=3800)
hxmax = Sensor("hxmax", initval=9999) 

rawhx = Sensor("rawhx", initval=0.0, diff=2, poll=50, callback=hxread)

for i in range(6):
    print(rawhx.values)
    time.sleep_ms(500)

print("After loop: ",rawhx.value)
k = Sensor("k", initval=.542)
offset = Sensor("offset", initval=rawhx.value)
print("Offset: ",offset.value)

scale = Sensor("scale", initval=0, diff=.2, poll = 500, callback=adjusttoscale)

tare = Sensor("tare", "IN", 5)
sleep = Sensor("sleep", initval=time.ticks_ms(), diff=30000)

def resetsleep():
    sleep.value = time.ticks_ms()
    time.sleep_ms(20)

# Called from main.py
def main():
    resetsleep()
    Sensor.MQTTSetup("foodscale")
    while True:
        Sensor.Spin()
        if tare.triggered:
            tare.triggered = False
            if tare.state:
                tm.show('tare')
                offset.setvalue(rawhx.value)
                resetsleep()
        if bunits.triggered:
            bunits.triggered = False
            if bunits.state:
                units.setstate(not units.state)
                resetsleep()
        if time.ticks_ms() - sleep.value > (sleep.diff + 10000):
            scale.timer.deinit()
            tm.show('    ',False)
            deepsleep()
