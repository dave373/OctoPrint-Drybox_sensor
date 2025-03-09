from machine import Pin, SoftI2C
from ahtx0 import AHT10
import time
  
i2c = SoftI2C(scl=Pin(10),sda=Pin(9))
pV = Pin(12,Pin.OUT, value=1)
pN = Pin(11,Pin.OUT, value=0)

sensor1 = AHT10(i2c)
sensor2 = AHT10(i2c, 0x39)
samples = 1
while 1:
    start = time.ticks_ms()
    print(samples, sensor1.data(samples), sensor2.data(samples), time.ticks_diff(time.ticks_ms(),start)/samples)
    samples+=1
    

