import neopixel
from machine import Pin, SoftI2C
from ahtx0 import AHT10
import time

np = neopixel.NeoPixel(machine.Pin(16),1)
i2c = SoftI2C(scl=Pin(10),sda=Pin(9))
pV = Pin(12,Pin.OUT, value=1)
pN = Pin(11,Pin.OUT, value=0)

sensor = AHT10(i2c)
while 1:
    print("T:%0.2fC,H:%0.2f%%" %(sensor.temperature, sensor.relative_humidity))
    if sensor.temperature > 60:
        np[0] = (255,0,0)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)
    elif sensor.temperature > 50:
        np[0] = (255,128,0)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)
    elif sensor.temperature > 40:
        np[0] = (128,128,0)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)
    else:
        np[0] = (0,255,0)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)

    if sensor.relative_humidity > 30:
        np[0] = (255,0,0)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)
    elif sensor.relative_humidity > 25:
        np[0] = (255,128,0)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)
    elif sensor.relative_humidity > 20:
        np[0] = (128,128,0)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)
    else:
        np[0] = (0,0,255)
        np.write()
        time.sleep(1)
        np[0] = (0,0,0)
        np.write()
        time.sleep(1)
    time.sleep(1)