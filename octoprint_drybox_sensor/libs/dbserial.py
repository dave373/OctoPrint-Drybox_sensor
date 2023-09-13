import serial
import threading
import time

class DBSerial(threading.Thread):

  def __init__(self, port, dbpi):
    threading.Thread.__init__(self)
    self._port = port
    self.logger = dbpi._logger
    self.pm = dbpi._plugin_manager
    self.dbpi = dbpi
    self.temp = 0
    self.humid = 0
    self.ph = None
    self.history = []
    self.hist_length = 10
    self.hist_delay = 86400 #24h

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
      self.logger.info(" ::DBSerial:: %s" %txt)
    else:
      print(txt)

  def open(self):
    try:
      if self._port == "debug":
        self.ph = "debug"
        self.log("DEBUG endpoint is being used")
      else:
        self.ph = serial.Serial(self._port)
        self.log("Opened the port : %s" %self._port)
    except Exception as e:
      self.log("Failed to open sensor port")
      self.ph = None
      return False
    return self.ph
    
  def close(self):
    if self.ph != "debug":
      self.ph.close()

  def readData(self):
    if self.ph == "debug":
      time.sleep(3)
      return "T:25.00C,H:25.00%\r\n"
    self.ph.readline().decode()

  def run(self):
    try:
      self.done = False
      if self.open() is not False:
        self.log("Starting Serial read thread")
        while not self.done:
          #self.log("Reading data in thread")
          dstr = self.readData()
          if dstr != "":
            try:
              data = dstr.strip().split(",")
              self.temp = float(data[0][2:7])
              self.humid = float(data[1][2:7])
              self.addHistData()
              self.log("SendingPM message %0.2f %0.2f" %(self.temp,self.humid))
              self.pm.send_plugin_message(
                self.dbpi._identifier, dict(temp=self.temp, humid=self.humid, history=self.history)
              )
            except Exception as e:
              self.log("Failed to parse data from %s : %s" %(dstr,e))
    except KeyboardInterrupt:
      self.log("Caught a ctrl-C... shutdown time")
      self.done=True
      self.close() 

  def stop(self):
    self.done = True

  def addHistData(self):
    if len(self.history) == 0:
      # initial entry
      self.history.append({"ts":time.time(),"temp":self.temp,"humid":self.humid})
    else:
      lastData = self.history[-1]["ts"]
      if (lastData + self.hist_delay) < time.time():
        # Store the new value
        self.history.append({"ts":time.time(),"temp":self.temp,"humid":self.humid})
      if len(self.history) > self.hist_length:
        self.history.pop(0)

if __name__ == "__main__":
  dbs = DBSerial('debug')

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
  print("Waiting for thread to stop")
  dbs.stop()
  dbs.join()
