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
from datetime import timedelta, datetime 

class DBSerial(threading.Thread):

    data_ids = {
        'TS' : 0,
        'TI' : 1,
        'HI' : 2,
        'TE' : 3,
        'HE' : 4
    }
    RRD_BU_FILE = ".octoprint/data/drybox/drybox.rrd"
    RRD_RAM_FILE = "/run/plugins/drybox.rrd"

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
            while not Path(self.RRD_RAM_FILE).parent.is_dir():
                self.log("Filesystem not ready for RAM RRD file... waiting for creation...")
                try:
                    Path(self.RRD_RAM_FILE).parent.mkdir(parents=True, exist_ok=True)
                except:
                    time.sleep(3)
            # We have the path, attempt to copy the existing data from disk to RAM File
            self.log("Loading disk RRD file")
            while self.loadRRDBUFile() is False:
                self.log("Failed to load RRD File, waiting for Filesystem?")
                time.sleep(5)
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

    def log(self, txt, mode="debug"):
        if self.logger is not None:
            if mode == "info":
                self.logger.info(" ::DBSerial:: %s" % txt)
            elif mode == "warn":
                self.logger.warn(" ::DBSerial:: %s" % txt)
                self.data['lastserialwarn']=txt
            else:
                self.logger.debug(" ::DBSerial:: %s" % txt)
        else:
            print("%s: %s" %(mode,txt))

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
            self.log("Copied blank RRD to disk file", 'warn')

    def dumpRRDBUFile(self):
        try:
            shutil.copyfile(self.RRD_RAM_FILE, self.RRD_BU_FILE)
            return True
        except Exception as e:
            self.log("Failed to dump RAM RRD file to disk: %s" % e, 'warn')
        return False

    def loadRRDBUFile(self):
        try:
            shutil.copyfile(self.RRD_BU_FILE, self.RRD_RAM_FILE)
            return True
        except Exception as e:
            self.log("Failed to load RRD disk file to RAM: %s" % e, 'warn')
        return False

    def updateRRDFile(self):
        if not os.path.isfile(self.RRD_RAM_FILE):
            if not self.loadRRDBUFile():
               # The RAM file does not exist?. and cannot be copid..create a new one???
               self.createRRD()
        rrdtool.update(self.RRD_RAM_FILE, 'N:%s:%s:%s:%s' %(self.data['TI'], self.data['TE'], self.data['HI'], self.data['HE']))

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
            self.log("Failed to open sensor port : %s" % e, 'warn')
            self.ph = None
            return False
        return self.ph

    def close(self):
        self.done = True
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
            self.log("Waiting for data...")
            try:
              dstr = self.ph.readline().decode()
              if dstr == "":
                  return False
              #self.log("Got data: %s" %dstr)
              data = dstr.strip().split(",")
              self.data['TS'] = time.time()
              for d in data:
                  self.data[d[:2]] = d[3:8]
              self.log("Read data: %s" %self.data)
            except Exception as e:
              self.log("Exception reading data.. %s" %e, 'warn')
              self.log(traceback.format_exc())
              self.temp = -2
              self.humid = -2
              return False
          
        return True 

    def get_history_data(self, span=None, start=None, dtype=None, count=0):
        results = None
        self.log("Get history: Span:%s start:%s dtype:%s count=%d" %(span, start, dtype,count))
        start_e,end_e = self.getEpochFromSpan(span, start)
        # What resolution?
        res = int((end_e-start_e)/count)
        self.log("using resolution of %d" %res)
        ds = "AVERAGE" if dtype is None else dtype
        try:
            self.log("Start and End specified, returning %d %s valuer from %s to %s" 
               %(res, ds, time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(start_e)),
               time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(end_e))))
            results = rrdtool.fetch(self.RRD_RAM_FILE, [ds, "-s", str(int(start_e)), "-e", str(int(end_e)), "-r", str(res)])
        except Exception as e:
            for dl in traceback.format_exc().split('\n'):
                self.log(dl)
        return results
       
    def getEpochFromSpan(self, span, start=None):
        tspan = None
        if 'h' in span:
            tspan = timedelta(hours=int(span.strip('h')))
        elif 'd' in span:
            tspan = timedelta(days=int(span.strip('d')))
        elif 'w' in span:
            tspan = timedelta(weeks=int(span.strip('w')))
        else:
            try:
                tspan = timedelta(minutes=int(span))
            except Exception:
                pass
        if tspan is None:
            # default to 1 day
            tspan = timedelta(days=1)
        start_dt = datetime.now()-tspan
        if start is not None and start != 0:
            start_dt = datetime.fromtimestamp(start) # Assume that start is suplied as an epoch
        end_dt = start_dt + tspan
        return start_dt.timestamp(), end_dt.timestamp()

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
                            self.log("Failed to read or send data in run loop : %s" % e, 'warn')
                            self.log(traceback.format_exc())
                    else:
                        time.sleep(0.5)
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
        self.log("Stopping the DBSerial thread", 'warn')
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
