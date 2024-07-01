import serial
import threading
import time
import random
import json
from pathlib import Path


class DBSerial(threading.Thread):

    HISTORY_FILE = "/home/pi/.octoprint/data/drybox/history.json"

    def __init__(self, port, dbpi=None):
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
        self.ts = 0
        self.ph = None
        self.history = []
        self.hist_length = 115200  # 4 days at 1 data point/5 secs
        self.hist_delay = 0  # capture everything
        self.send_history = False
        if not Path(self.HISTORY_FILE).parent.is_dir():
            Path(self.HISTORY_FILE).parent.mkdir(parents=True, exist_ok=True)

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
            self.logger.info(" ::DBSerial:: %s" % txt)
        else:
            print(txt)

    def write_data_file(self):
        try:
            with open(self.HISTORY_FILE, "w") as fh:
                json.dump(self.history, fh, indent=2)
        except Exception as e:
            self.log("Failed to write data file : %s" % e)

    def read_data_file(self):
        try:
            with open(self.HISTORY_FILE, "r") as fh:
                self.history = json.load(fh)
                self.log(
                    "Loaded history data from file of %d DPs from %s to %s"
                    % (
                        len(self.history),
                        time.ctime(self.history[0]["ts"]),
                        time.ctime(self.history[-1]["ts"]),
                    )
                )
        except Exception as e:
            self.log("Failed to read data file : %s" % e)

    def open(self):
        try:
            if self._port == "debug":
                self.ph = "debug"
                self.log("DEBUG endpoint is being used")
            else:
                self.ph = serial.Serial(self._port, timeout=10)
                self.log("Opened the port : %s" % self._port)
        except Exception as e:
            self.log("Failed to open sensor port : %s" % e)
            self.ph = None
            return False
        return self.ph

    def close(self):
        if len(self.history) > 1000:
            self.log("Writing history file before closing")
            self.write_data_file()
        else:
            self.log("history is short, not saving")
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
            except Exception as e:
                self.log("Exception reading data.. ", e)
                self.temp = -2
                self.humid = -2
                return False
            # self.log("Got data: %s" %dstr)
            data = dstr.strip().split(",")
            self.temp = float(data[0][2:7])
            self.humid = float(data[1][2:7])
            self.ts = time.time()
        return True

    def get_history_data(self, tspan, count=100):
        tspan = int(tspan)
        if count == 0:
            count = 100
        self.log("Getting data from tspan of %d" % tspan)
        results = []
        if not tspan:
            self.log("No tspan specified, so returning from all history")
            results = self.history[0 :: int(len(self.history) / count)]
        else:
            now = time.time()
            rec = time.time() - tspan
            self.log("NOW: %d   REC=%d  diff=%d" % (now, rec, now - rec))
            index = 0

            while int(self.history[index]["ts"]) < rec:
                index += 1
                if index >= len(self.history):
                    self.log(
                        "Reached the end of the history... How??  len=%d, ind=%d, rec=%d, last_ts=%d"
                        % (len(self.history), index, rec, self.history[index - 1]["ts"])
                    )
                    index -= 1
                    break
            if (count*2) <= len(self.history[index:]):
                self.log(
                    "Returning %d history points from %d available, from %d to %d"
                    % (count, len(self.history) - index, self.history[index]["ts"], now)
                )
                return self.history[index :: int(len(self.history[index:]) / count)]
            else:
                self.log(
                    "Returning all history points from the %d available, from %d to %d"
                    % (len(self.history) - index, self.history[index]["ts"], now)
                )
                return self.history[index:]


    def run(self):
        try:
            self.done = False
            self.log("Loading history data file")
            self.read_data_file()

            if self.open() is not False:
                self.log("Starting Serial read thread")
                while not self.done:
                    # self.log("Reading data in thread")
                    if self.read_data():
                        try:
                            self.add_hist_data()
                            if (
                                time.time() - Path(self.HISTORY_FILE).stat().st_mtime
                            ) > 86400:
                                self.write_data_file()
                            # self.log("Send_history is %s, AddHistData returned %s" %(self.send_history, sendhist))
                            if self.pm is not None:
                                #if self.send_history:
                                #    # self.log("Sending PM message with history %0.2f %0.2f Hist:[%d]" %(self.temp,self.humid,len(self.history)))
                                #    self.pm.send_plugin_message(
                                #        self.dbpi._identifier,
                                #        dict(
                                #            temp=self.temp,
                                #            humid=self.humid,
                                #            history=self.history,
                                #        ),
                                #    )
                                #    self.send_history = False
                            #    else:
                                    # self.log("Sending PM message %0.2f %0.2f" %(self.temp,self.humid))
                                self.pm.send_plugin_message(
                                    self.dbpi._identifier,
                                    dict(
                                        ts=self.ts, temp=self.temp, humid=self.humid
                                    ),
                                )
                        except Exception as e:
                            self.log("Failed to read or send data in run loop : %s" % e)
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

    def add_hist_data(self):
        if len(self.history) == 0:
            # initial entry
            self.history.append(
                {"ts": time.time(), "temp": self.temp, "humid": self.humid}
            )
            return True
        else:
            lastData = self.history[-1]["ts"]
            if (lastData + self.hist_delay) < time.time():
                # Store the new value
                self.history.append(
                    {"ts": time.time(), "temp": self.temp, "humid": self.humid}
                )
                if len(self.history) > self.hist_length:
                    self.history.pop(0)
                return True
            # else :
            #  self.log("Next history update in %0.0f seconds" %((lastData + self.hist_delay)-time.time()))
        return False

    if __name__ == "__main__":

        dbs = DBSerial("debug")

        dbs.start()
        time.sleep(1)
        print("Starting test")
        while 1:
            try:
                print(
                    "Temp: %0.2f   Humid: %0.2f  History length=%d"
                    % (dbs.getTemp(), dbs.getHumid(), len(dbs.history))
                )
                time.sleep(5)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print("Something went wrong : %s" % e)
                break
        print("Waiting for thread to stop")
        dbs.stop()
        dbs.join()
