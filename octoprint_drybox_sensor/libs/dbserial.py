import os
import serial
import threading

class DBSerial(threading.Thread):

  def __init__(self, port, logger = None):
    threading.Thread.__init__(self)
    self._port = port
    self.logger = logger
    self.temp = 0
    self.humid = 0
    self.ph = None

  def getTemp(self):
    if self.ph is not None:
      return self.temp
    else:
      raise ConnectionError("Not connected")

  def getHumid(self):
    if self.ph is not None:
      return self.humid
    else:
      raise ConnectionError("Not connected")
    
  def log(self, txt):
    if self.logger is not None:
      self.logger.info(" ::DBSerial:: ", txt)
    else:
      print(txt)

  def open(self):
    try:
      self.ph = serial.Serial(self._port)
    except Exception as e:
      self.log("Failed to open sensor port")
      self.ph = None
      return False
    return self.ph
    
  def close(self):
    self.ph.close()

  def run(self):
    self.done = False
    if self.open() is not False:
      while not self.done:
        dstr = self.ph.readline().decode()
        if dstr != "":
          try:
            data = dstr.strip().split(",")
            self.temp = float(data[0][2:7])
            self.humid = float(data[1][2:7])
          except:
            self.log("Failed to parse data from %s" %dstr)

  def stop(self):
    self.done = True
        

if __name__ == "__main__":
  import time
  dbs = DBSerial('/dev/ttyACM0')

  dbs.start()

  while 1:
    try:
      print ("Temp: %0.2f   Humid: %0.2f" %(dbs.getTemp(),dbs.getHumid()))
      time.sleep(5)
      
    except KeyboardInterrupt:
      break
    except Exception as e:
      print("Something went wrong : %s" %e)
      break
    
