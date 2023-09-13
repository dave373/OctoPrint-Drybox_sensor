import serial
import threading
import time
import random

class DBSerial(threading.Thread):

  def __init__(self, port, dbpi = None):
    threading.Thread.__init__(self)
    self._port = port
    self.logger = None
    self.pm = None
    self.dbpi = dbpi
    if dbpi is not None:
      self.logger = dbpi._logger
      self.pm = dbpi._plugin_manager
      self.dbpi = dbpi
    self.temp = 0
    self.humid = 0
    self.ph = None
    self.history = []
    self.hist_length = 10
    self.hist_delay = 86400 #24h
    self.send_history = False

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
      self.temp = random.random()*30+20
      self.humid = random.random()*50+10
    else:
      dstr = self.ph.readline().decode()
      data = dstr.strip().split(",")
      self.temp = float(data[0][2:7])
      self.humid = float(data[1][2:7])
      

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
              sendhist = self.addHistData()
              #self.log("Send_history is %s, AddHistData returned %s" %(self.send_history, sendhist))
              if self.pm is not None:
                if sendhist or self.send_history:
                  #self.log("Sending PM message with history %0.2f %0.2f Hist:[%d]" %(self.temp,self.humid,len(self.history)))
                  self.pm.send_plugin_message(
                    self.dbpi._identifier, dict(temp=self.temp, humid=self.humid, history=self.history)
                  )
                  self.send_history = False
                else:
                  #self.log("Sending PM message %0.2f %0.2f" %(self.temp,self.humid))
                  self.pm.send_plugin_message(
                    self.dbpi._identifier, dict(temp=self.temp, humid=self.humid)
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
      return True
    else:
      lastData = self.history[-1]["ts"]
      if (lastData + self.hist_delay) < time.time():
        # Store the new value
        self.history.append({"ts":time.time(),"temp":self.temp,"humid":self.humid})
        if len(self.history) > self.hist_length:
          self.history.pop(0)
        return True
      #else :
      #  self.log("NExt history update in %0.0f seconds" %((lastData + self.hist_delay)-time.time()))
    return False
    

if __name__ == "__main__":

  dbs = DBSerial('/dev/ttyACM0')

  dbs.start()
  time.sleep(1)
  print("Starting test")      
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
