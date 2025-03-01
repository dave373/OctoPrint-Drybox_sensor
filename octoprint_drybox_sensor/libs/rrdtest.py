#rrdtest
import rrdtool
rrdfile = "/home/pi/.octoprint/data/drybox/drybox.rrd"

rrdtool.create(rrdfile,
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


