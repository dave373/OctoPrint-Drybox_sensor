import serial
import threading
import time
import random
import json
import os
import shutil
from pathlib import Path
import rrdtool
import traceback


class DBSerial(threading.Thread):

    data_ids = {
        'TS' : 0,
        'TI' : 1,
        'HI' : 2,
        'TE' : 3,
        'HE' : 4
    }
    RRD_BU_FILE = ".octoprint/data/drybox/drybox.rrd"
    RRD_RAM_FILE = "/run/user/1000/drybox.rrd"

    def __init__(self, port, dbpi=None, home_path=None):
        threading.Thread.__init__(self)
        self._port = port
        self.logger = None
        self.pm = None
        self.dbpi = dbpi
        if dbpi is not None:
            self.logger = dbpi._logger
            self.pm = dbpi._plugin_manager
            self.dbpi = dbpi

        self.data = {}
        for id in self.data_ids:
            self.data[id] = 0
        self.ph = None
        if home_path is None:
            self.RRD_BU_FILE = os.path.join(os.environ['HOME'],self.RRD_BU_FILE)
        else:
            self.RRD_BU_FILE = os.path.join(home_path,self.RRD_BU_FILE)
        if not Path(self.RRD_BU_FILE).parent.is_dir():
            Path(self.RRD_BU_FILE).parent.mkdir(parents=True, exist_ok=True)
            # The directory doesn't exist, so the RRD file must not either
        else:
            # We have the path, attempt to copy the existing data from disk to RAM File
            self.log("Loading disk RRD file")
            self.loadRDDBUFile()

        if not os.path.isfile(self.RRD_RAM_FILE):
            # The RAM file does not exist?.  create a new one!
            self.createRRD()

    def getData(self, id=None):
        if self.ph is not None:
            if id is None:
                return self.data
            if id in self.data:
                return self.data[id]
        else:
            raise ConnectionError("Not connected")

    def log(self, txt):
        if self.logger is not None:
            self.logger.info(" ::DBSerial:: %s" % txt)
        else:
            print(txt)

    def createRRD(self):
        # These settings create a ~12MB file
        # TODO: Make settings adjustable through GUI config
        rrdtool.create(self.RRD_RAM_FILE,
          "--start","now","--step","5",
          "DS:int_temp:GAUGE:60:-10:100",
          "DS:ext_temp:GAUGE:60:-10:100",
          "DS:int_humid:GAUGE:60:0:100",
          "DS:ext_humid:GAUGE:60:0:100",
          "RRA:AVERAGE:0.5:1m:7d",
          "RRA:AVERAGE:0.5:5m:3M",
          "RRA:AVERAGE:0.5:1h:2y",
          "RRA:MIN:0.5:5s:7d",
          "RRA:MIN:0.5:5m:3M",
          "RRA:MIN:0.5:1h:2y",
          "RRA:MAX:0.5:5s:7d",
          "RRA:MAX:0.5:5m:3M",
          "RRA:MAX:0.5:1h:2y",
        )
        if not os.path.isfile(self.RRD_BU_FILE):
            self.dumpRRDBUFile()
            self.log("Copied blank RRD to disk file")

    def dumpRRDBUFile(self):
        try:
            shutil.copyfile(self.RRD_RAM_FILE, self.RRD_BU_FILE)
        except Exception as e:
            self.log("Failed to dump RAM RRD file to disk: %s" % e)

    def loadRDDBUFile(self):
        try:
            shutil.copyfile(self.RRD_BU_FILE, self.RRD_RAM_FILE)
        except Exception as e:
            self.log("Failed to load RRD disk file to RAM: %s" % e)

    def updateRRDFile(self):
        rrdtool.update(self.RRD_RAM_FILE, 'N:%s:%s:%s:%s' %(self.data['TI'], self.data['TE'], self.data['HI'], self.data['HE']))
        #TODO Check age of disk file, copt to disk if over [x] time

    def open(self):
        try:
            if self._port == "debug":
                self.ph = "debug"
                self.log("DEBUG endpoint is being used")
            else:
                self.ph = serial.Serial(self._port, timeout=1)
                self.log("Opened the port : %s" % self._port)
                self.ph.flush()
                self.log("Flushing old values...")
                while len(self.ph.read_until(b'\n')) > 2:
                    time.sleep(0.1)
                self.log("Flush complete")

        except Exception as e:
            self.log("Failed to open sensor port : %s" % e)
            self.ph = None
            return False
        return self.ph

    def close(self):
        self.log("Writing RRD file to disk before closing")
        self.dumpRRDBUFile()
        if self.ph != "debug":
            self.ph.close()

    def read_data(self):
        if self.ph == "debug":
            time.sleep(3)
            self.temp = random.random() * 30 + 20
            self.humid = random.random() * 50 + 10
            self.ts = time.time()
        else:
            # self.log("Waiting for data...")
          try:
              dstr = self.ph.readline().decode()
              if dstr == "":
                  return False
              #self.log("Got data: %s" %dstr)
              data = dstr.strip().split(",")
              self.data['TS'] = time.time()
              for d in data:
                  self.data[d[:2]] = d[3:8]
          except Exception as e:
              self.log("Exception reading data.. %s" %e)
              self.log(traceback.format_exc())
              self.temp = -2
              self.humid = -2
              return False
          
        return True

    def get_history_data(self, start=None, end=None, dtype=None):
        results = None
        ds = "AVERAGE" if dtype is None else dtype
        if start is None and end is None:
          self.log("Getting %s data, 1 day" %(ds))
          results = rrdtool.fetch(self.RRD_RAM_FILE, ds)
        if start is not None and end is None:
          self.log("Start specified, returning %s from (%d) %s" %(ds, int(start), time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(start))))
          results = rrdtool.fetch(self.RRD_RAM_FILE, [ds, "-s",  str(int(start))])
        elif start is not None and end is not None:
          self.log("Start and End specified, returning %s from %s to %s" 
                   %(ds, time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(start)),
                   time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(end))))
          results = rrdtool.fetch(self.RRD_RAM_FILE, [ds, "-s", str(int(start)), "-e", str(int(end))])
        return results
        
    def run(self):
        try:
            self.done = False
            
            if self.open() is not False:
                self.log("Starting Serial read thread")
                while not self.done:
                    # self.log("Reading data in thread")
                    if self.read_data():
                        try:
                            self.updateRRDFile()
                            if (
                                time.time() - Path(self.RRD_BU_FILE).stat().st_mtime
                            ) > 86400:
                                self.dumpRRDBUFile()
                            if self.pm is not None:
                                self.pm.send_plugin_message(
                                    self.dbpi._identifier, self.data
                                )
                        except Exception as e:
                            self.log("Failed to read or send data in run loop : %s" % e)
                            self.log(traceback.format_exc())
                    else:
                        time.sleep(0.99)
            else:
                # Failed to open port
                if self.pm is not None:
                    self.pm.send_plugin_message(
                        self.dbpi._identifier, dict(temp=-1, humid=-1)
                    )
                else:
                    self.log("Failed to open port : %s" % self._port)
                self.done = True
        except KeyboardInterrupt:
            self.log("Caught a ctrl-C... shutdown time")
            self.done = True
        self.close()

    def stop(self):
        self.done = True

    
if __name__ == "__main__":
  dbs = DBSerial("/dev/ttyACM0")

  dbs.start()
  time.sleep(1)
  print("Starting test loop")
  while 1:
      try:
          data = dbs.get_history_data(start=time.time()-600, dtype="MAX")

          print(data[0], data[1])
          for i in range(len(data[2])):
              if data[2][i][0] is not None:
                  print("%3d %d : %s" %(i,data[0][0] + i*data[0][2], data[2][i]))
          time.sleep(5)

      except KeyboardInterrupt:
          break
      except Exception as e:
          print("Something went wrong : %s" % e)
          print(traceback.format_exc())
          break
  print("Waiting for thread to stop")
  dbs.stop()
  dbs.join()
