import neopixel
from machine import Pin, SoftI2C
from ahtx0 import AHT10
import time
import uselect
import sys
import math
  
global brightness
global read_delay
global led_time


np = neopixel.NeoPixel(machine.Pin(16),1)
i2c = SoftI2C(scl=Pin(10),sda=Pin(9))
pV = Pin(12,Pin.OUT, value=1)
pN = Pin(11,Pin.OUT, value=0)

class TH_Sensor():
    
    def __init__(self, name, i2c, address=None, temp_levels=None, humid_levels=None):
        self.name = name
        self.sensor = AHT10(i2c, address=address)
        self.temp_levels = [5,35,40,50] if temp_levels is None else temp_levels
        self.humid_levels = [5,20,25,30] if humid_levels is None else humid_levels
        self.temp = None
        self.humid = None
        
    def read(self):
        self.temp = self.sensor.temperature
        self.humid = self.sensor.relative_humidity
        
    def getTempState(self):
        ''' Returns 1 for good, 2 for warn, 3 for high, 0 for low '''
        for i in range(len(self.temp_levels)):
            if self.temp < self.temp_levels[i]:
                return i
    
    def getHumidState(self):
        ''' Returns 1 for good, 2 for warn, 3 for high, 0 for low '''
        for i in range(len(self.humid_levels)):
            if self.humid < self.humid_levels[i]:
                return i
    
def setLED(level):
    global brightness
    #print("LED: %s" %level)
    rgb = (0,0,0)
    if level == 'good':
        rgb = (math.ceil(brightness/2),math.ceil(brightness/2),math.ceil(brightness/2))
    elif level == 0:
        # Low ... Blue
        rgb = (0,0,)
    elif level == 1:
        # OK ... Green
        rgb = (0,brightness, 0)
    elif level == 2:
        # Warn ... Orange
        rgb = (brightness,brightness,0)
    elif level == 3:
        # High ... Red
        rgb = (brightness,0,0)
    elif level == 10:
        # RECV ... PURPLE
        rgb = (brightness,0,brightness)    
    np[0] = rgb
    np.write()
    
def commandList():
    print('## Command List ##')
    print('#   "BR<val>"   Set brightness - INT 1-255')
    print('#   "TI<i><val>"   Set Internal Temp Levels - <INT index 0-3 low/good/warn/high> <INT value degC>')
    print('#   "HI<i><val>"   Set Internal Humidity Levels - INT <low/good/warn/high><value RH%>') 
    print('#   "TE<i><val>"   Set External Temp Levels - INT <low/good/warn/high><value degC>')
    print('#   "HE<i><val>"   Set External Humidity Levels - INT <low/good/warn/high><value RH%>') 
    print('#   "RD<sec>"      Set Read Delay - INT Seconds between readings')
    print('#   "LT<msec>"     Set LED_TIME - INT msec per status flash')
    print('#   e.g.  Internal Humidity good upper level to 15% = HI115')
    

STATE_MEASURE = 1
STATE_SEND = 2
STATE_INT_T_LED = 3
STATE_INT_H_LED = 4
STATE_EXT_T_LED = 5
STATE_EXT_H_LED = 6
STATE_END = 7

brightness = 10 # 1-255
read_delay = 5  # Seconds
led_time = 500 # msec

ext_sensor = TH_Sensor('ext', i2c, None, [0,35,40,45], [5,50,70,90])
int_sensor = TH_Sensor('int', i2c, 0x39, [10,35,40,45], [5,15,25,40])

spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)

state = 0
led_state = 0
last_read = 0
next_state_time = time.ticks_add(time.ticks_ms(), 1)
while 1:
    #print(time.ticks_diff(time.ticks_ms(), next_state_time))
    while time.ticks_diff(time.ticks_ms(), next_state_time) < 0:        
        cmd = ''
        while spoll.poll(0):
            setLED(10)
            cmd += sys.stdin.read(1)
            time.sleep_ms(1)
        if cmd != '':
            try:
                cmd = cmd.strip()
                if cmd == "":
                    continue
                print("# CMD:RCVD:%s" %cmd)
                if cmd == "LI" or cmd == "?" or cmd == "help" or cmd == "-h":
                   commandList()
                   continue
                if cmd[2:] and not cmd[2:].strip("01234567890"):
                    if cmd.startswith('BR'):
                        # Set brightness
                        brightness = int(cmd[2:])
                    elif cmd.startswith('TI'):
                        # Set Internal Temp Level
                        int_sensor.temp_levels[int(cmd[2])] = int(cmd[3:])
                    elif cmd.startswith('HI'):
                        # Set Internal Temp Level
                        int_sensor.humid_levels[int(cmd[2])] = int(cmd[3:])
                    elif cmd.startswith('TE'):
                        # Set Internal Temp Level
                        ext_sensor.temp_levels[int(cmd[2])] = int(cmd[3:])
                    elif cmd.startswith('HE'):
                        # Set Internal Temp Level
                        ext_sensor.humid_levels[int(cmd[2])] = int(cmd[3:])
                    elif cmd.startswith('RD'):
                        # Set Read Delay
                        read_delay = int(cmd[2:])
                    elif cmd.startswith('LT'):
                        # Set LED_TIME
                        led_time = int(cmd[2:])
                    else:
                        print("# CMD:RESULT:UNKNOWN:%s" %cmd)
                    print("# CMD:RESULT:OK")
            except Exception as e:
                print("# CMD:RESULT:FAIL:%s" %str(e).replace(' ','_'))
                
                
    if np[0] != (0,0,0):
        np[0] = (0,0,0)
        np.write()
        time.sleep_ms(int(led_time*0.1))
    
    state+=1
    if state > STATE_END:
        state = STATE_MEASURE
    if state == STATE_MEASURE:  
        # Get measurements
        ext_sensor.read()
        int_sensor.read()
        last_read = time.ticks_ms()
    elif state == STATE_SEND:
        print("TI:%0.2fC,HI:%0.2f%%,TE:%0.2fC,HE:%0.2f%%" %(int_sensor.temp, int_sensor.humid, ext_sensor.temp, ext_sensor.humid))
    elif state == STATE_INT_T_LED:
        setLED(int_sensor.getTempState())
        next_state_time = time.ticks_add(time.ticks_ms(), led_time)    
    elif state == STATE_INT_H_LED:
        setLED(int_sensor.getHumidState())
        next_state_time = time.ticks_add(time.ticks_ms(), led_time)    
    elif state == STATE_EXT_T_LED:
        setLED(ext_sensor.getTempState())
        next_state_time = time.ticks_add(time.ticks_ms(), led_time)
    elif state == STATE_EXT_H_LED:
        setLED(ext_sensor.getHumidState())
        next_state_time = time.ticks_add(time.ticks_ms(), led_time)
    elif state == STATE_END:
        setLED('good')
        next_state_time = time.ticks_add(last_read, read_delay*1000)
    
        