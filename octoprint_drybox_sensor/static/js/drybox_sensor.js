/*
 * View model for OctoPrint-Drybox_sensor
 *
 * Author: David Haddon
 * License: AGPLv3
 */
$(function() {
    function Drybox_sensorViewModel(parameters) {
        var self = this;
        self.tdata = [];

        // assign the injected parameters, e.g.:
        self.settings = parameters[0];
        self.settingsViewModel = parameters[1];
        
        self.dryboxTemp = ko.observable();
        self.dryboxHumid = ko.observable();
        self.dryboxHistory = ko.observable();
        self.dryboxExtTemp = ko.observable();
        self.dryboxExtHumid = ko.observable();
        
        //console.log("DRYBOX SETTINGS!!!!!");
        //console.log(self.settings);
        //console.log(self.settingsViewModel);

        self.onDataUpdaterPluginMessage = function (plugin, data) {
          console.log("Drybox sensor data update : " + plugin);
          console.log(data);
          //for (d in data) {
          //  console.log(d + " : " + data[d]);
	        //}
          if (plugin != "drybox_sensor") {
              return;
          }
	      if (data.TI == -1 && data.HI == -1) {
	        // Connection error. 
            $('#drybox-temp').html("Not Connected").addClass("drybox_error");
            $('#drybox-humid').hide();
          }
          else if (data.TI == -2 && data.HI == -2) {
            // Data Timeout error. 
              $('#drybox-temp').html("Data Timeout").addClass("drybox_error");
              $('#drybox-humid').hide();
          }  
          else {
            $('#drybox-humid').show();
            if (data.TI) {
              $('#drybox-temp').html(_.sprintf("%.1f&deg;C", data.TI)).removeClass("drybox_error drybox_warn");
              if (data.TI > self.settings.settings.plugins.drybox_sensor.int_temp_error()) {
                $('#drybox-temp').addClass("drybox_error");
              }
              else if (data.TI > self.settings.settings.plugins.drybox_sensor.int_temp_warn()) {
                $('#drybox-temp').addClass("drybox_warn");
              }
              
            }
            if (data.HI) {
              $('#drybox-humid').html(_.sprintf("%.1f%%", data.HI)).removeClass("drybox_error drybox_warn");
              if (data.HI > self.settings.settings.plugins.drybox_sensor.int_humid_error()) {
                $('#drybox-humid').addClass("drybox_error");
              }
              else if (data.HI > self.settings.settings.plugins.drybox_sensor.int_humid_warn()) {
                $('#drybox-humid').addClass("drybox_warn");
              }
              
            }
            if (data.TE) {
              $('#drybox-ext-temp').html(_.sprintf("%.1f&deg;C", data.TE)).removeClass("drybox_error drybox_warn");
              if (data.TE > self.settings.settings.plugins.drybox_sensor.ext_temp_error()) {
                $('#drybox-ext-temp').addClass("drybox_error");
              }
              else if (data.TE > self.settings.settings.plugins.drybox_sensor.ext_temp_warn()) {
                $('#drybox-ext-temp').addClass("drybox_warn");
              }
              
            }
            if (data.HE) {
              $('#drybox-ext-humid').html(_.sprintf("%.1f%%", data.HE)).removeClass("drybox_error drybox_warn");
              if (data.HE > self.settings.settings.plugins.drybox_sensor.ext_humid_error()) {
                $('#drybox-ext-humid').addClass("drybox_error");
              }
              else if (data.HE > self.settings.settings.plugins.drybox_sensor.ext_humid_warn()) {
                $('#drybox-ext-humid').addClass("drybox_warn");
              }
              
            } 
          }
        }
        
        self.printTextHistory = function() {
            html = "<ul class='drybox-histlist'>";
            var textskip = Math.floor(data.history.length/50);
            var count = 0;
            for (h in data.history) {
              var d = new Date(data.history[h]['ts']*1000);
              if (count%textskip == 0) {
                 
                  html += "<li>" + d.toLocaleString() + "  ";
                  tclass = "";
                  if (data.history[h]['temp'] > parseInt(self.settings.settings.plugins.drybox_sensor.temp_error())) {
                    tclass = "drybox_error";
                  }
                  else if (data.history[h]['temp'] > parseInt(self.settings.settings.plugins.drybox_sensor.temp_warn())) {
                    tclass = "drybox_warn"; 
                  }
                  
                  html += "<b class='" + tclass + "'>" + _.sprintf("%3.1f&deg;C", data.history[h]['temp']) + "</b>";
                  hclass = "";
                  if (data.history[h]['humid'] > self.settings.settings.plugins.drybox_sensor.humid_error()) {
                    hclass = "drybox_error";
                  }
                  else if (data.history[h]['humid'] > self.settings.settings.plugins.drybox_sensor.humid_warn()) {
                    hclass = "drybox_warn";
                  }
                                    html += "<b class='" + hclass + "'>" + _.sprintf("%3.1f%%", data.history[h]['humid']) + "</b></li>\n";
              }
              count++;
            }
            html += "</ul>"
            $('#drybox-history').html(html);
        }
       

        self.onBeforeBinding = function() {
          //self.settings = self.global_settings.settings.plugins.drybox_sensor;
          console.log("DRYBOX: On Before Binding : " + self.global_settings);
        }

        self.onShutdown = function() {
            console.log("DRYBOX SHUTDOWN!!!");
        }
        
	    self.onShowHideDryBox = function(oc) {
            console.log("OSHDB: " + oc);
	        if ($('#drybox-history-div').is(':visible') && oc == "close")  {
		        $('#drybox-history-div').hide();
	        }
            else {
		        $('#drybox-history-div').show();
                $('#db1w').click();
                $('#drybox-graph-image').show();
                $('#drybox-graph-image').width=$('#drybox-history-div').width-10;
                $('#drybox-graph-image').height=$('#drybox-history-div').height-100;
              
	        }
	    }

	    self.showDryBoxHistText = function(event) {
	        $('#drybox-history-scroll').toggle();
	        $('#drybox-graph').toggle();
	        $('#drybox-graph-legend').toggle();
            self.printTextHistory();
	        event.stopPropagation();
	   
	    }

	    self.dryboxGraphTimeSpan = function(event) {
            var start = 0;
            var span = 0; 
            if (event == "custom") {
                console.log("Custom time.... WIP");
                start = $('#db_customStart').val();
                span = $('#db_custoomSpan').val();
            }
            else {
                event.stopPropagation();	   
                start = 0;
                span = event.target.value;
            }
            console.log("Graphing: start = " + start + "  Span = " + span);
            var canvas = document.getElementById("drybox-graph");
            var dtype = "AVERAGE";

            $.ajax({
                url:         "/api/plugin/drybox_sensor",
                type:        "POST",
                contentType: "application/json",
                dataType:    "json",
                headers:     {"X-Api-Key": UI_API_KEY},
                data:        JSON.stringify({ "command": "graph_tspan", "tspan": span , "start": start, "dtype":dtype, "count" : canvas.width}),
                complete: function(data) {
                    console.log("POSt completed: ");
                    console.log(data);
                    self.tdata=data.responseJSON;
                    self.draw_drybox_graph();
                }
            });
        }

            
        self.draw_drybox_graph = function() {
		
            var canvas = document.getElementById("drybox-graph");
            var cdiv = document.getElementById("drybox-history-div");
            canvas.width = cdiv.offsetWidth*.95;
            canvas.height = cdiv.offsetHeight*0.8;
            var context = canvas.getContext("2d");
            
            console.log("DRYBOX Canvas size: " + canvas.width + "x" + canvas.height);
            dp = []
            console.log("Timespan: " + self.tdata[0]);
            console.log("Names: " + self.tdata[1]);
            console.log("Data Len: " + self.tdata[2].length);
            var start_ts = self.tdata[0][0];
            var end_ts = self.tdata[0][1];
            var ts_step = self.tdata[0][2];        
            var tspan = self.tdata[0][1] - self.tdata[0][0];
            
            for (tdind in self.tdata[2]) {
              var td = self.tdata[2][tdind];
              // add each value to dp for min max
              if (td[0] != null && td[2] != null) {
                  dp.push(td[0],td[1],td[2],td[3]);
              }
            }
            var maxv = Math.max(...dp);
            var minv = Math.min(...dp);
            var MAX_SCALE = Math.floor(maxv+(5-(maxv%5)));
            var MIN_SCALE = Math.floor(minv-(minv%5));
            
            var LABEL_WIDTH=60;
            var LABEL_HEIGHT=15;

            var graph_height = canvas.height - LABEL_HEIGHT;
            var graph_width = canvas.width - LABEL_WIDTH;
            //clear the canvas
            context.clearRect(0, 0, canvas.width, canvas.height);
            context.moveTo(0, 0);
            // setup colours and fill for each plot (TI, TE, HI, HE)
            var colours=[["#FF0000","rgba(255, 0, 0, 0.1"],["#884400","rgba(128,64,0,0.1"],["#0000FF","rgba(0,0,255,0.1)"],["#004488","rgba(0,64,128,0.1"]];
            // Work out the timebase...  oldest on left so 0 = tdata[0][1]
            var tb_ratio = (tspan / graph_width); 
            //draw the graph line for each data series
          
            for (var di = 0; di<4 ; di++) {
                var name = self.tdata[1][di];
                context.beginPath();
                context.lineWidth = 1;
                context.strokeStyle = colours[di][0];
                for(var i = 0; i < self.tdata[2].length; i++){
                    if (self.tdata[2][i][di] != null) {
                        var vertpx = canvas.height - (graph_height * (self.tdata[2][i][di]-MIN_SCALE) / (MAX_SCALE-MIN_SCALE))-LABEL_HEIGHT;
                        context.lineTo((i * ts_step)/tb_ratio, vertpx); 
                        if (i%100 == 0) {
                            console.log("Data[" + i + "][" + self.tdata[1][di] + "] = " + self.tdata[2][i][di] + "  LINE TO: " + (graph_width - (i * ts_step)/tb_ratio).toFixed(1) + "," + vertpx.toFixed(1));
                        }
                    }
                    else {
                        //context.moveTo(graph_width - (i * ts_step)/tb_ratio, lastval);
                        if (i%100 == 0) {
                            console.log("Data[" + i + "][" + self.tdata[1][di] + "] = " + self.tdata[2][i][di] + "  SKIPPED!!! ");
                        }

                    }
                    
                }
                context.stroke();

                //fill under data
                /*context.fillStyle = colours[di][1];
                context.lineTo(canvas.width - LABEL_WIDTH-1, graph_height);
                context.lineTo(1, graph_height);
                context.closePath();
                context.fill();
                */
            }
           

            //outline frame
            context.strokeStyle = "#222222";
            context.strokeRect(0, 0, canvas.width - LABEL_WIDTH, graph_height);
            
            //Vertical markers
            context.beginPath();
            context.strokeStyle = "#444444";
            context.lineWidth = 0.2;
            var horizontalLine = graph_height / 10;
           
            for (let index = 1; index < 10; index++) {
                context.moveTo(0, horizontalLine * index);
                context.lineTo(canvas.width - LABEL_WIDTH, (horizontalLine * index) + 0.2);
                context.font = "14px arial";
                context.fillStyle = "black"
                context.fillText((MAX_SCALE - (index * ((MAX_SCALE-MIN_SCALE)/10))).toFixed(1) + "\u2103/%", canvas.width - LABEL_WIDTH + 3, (horizontalLine * index) + graph_height/50, LABEL_WIDTH);
                context.moveTo(0, 0);
                
            }
            context.fillText(MIN_SCALE.toFixed(1) + "\u2103/%", canvas.width - LABEL_WIDTH + 3, graph_height -0.8 );
            context.fillText(MAX_SCALE.toFixed(1) + "\u2103/%", canvas.width - LABEL_WIDTH + 3, 14);
            context.stroke();

            // Time Markers
            context.beginPath();
            context.strokeStyle = "#444444"
            context.lineWidth = 0.2;
            var lastmarkpos = -1;
            var lastmarkts = start_ts;
            var markcount = 6;

            for (let mindex = markcount; mindex >= 0 ; mindex--) {
                 
                 context.moveTo((canvas.width-LABEL_WIDTH)/(markcount) * mindex, 0);
                 context.lineTo((canvas.width-LABEL_WIDTH)/(markcount) * mindex, graph_height);
                 context.font = "14px serif";
                 context.fillStyle = "black";
                 var mts = (start_ts+(tspan/markcount*mindex))*1000;
                 console.log("Time Marker: " + mindex + " TS:" + mts);
                 var dt = new Date(mts);
                 var dstr = dt.getHours() + ":" + (dt.getMinutes() > 9 ? dt.getMinutes() : "0" + dt.getMinutes());   
                 if (tspan > 100000) { // More than a day
                    var dstr = (dt.getDate() + 1) + "/" + (dt.getMonth() + 1) + " " + dt.getHours() > 9 ? dt.getHours() : "0" + dt.getHours() + ":00";   
                 }
                 console.log("Marker String: " + dstr);
                 context.fillText(dstr,(canvas.width-LABEL_WIDTH)/markcount * mindex, canvas.height-5);	 
             
            }
            context.stroke();
        }
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Drybox_sensorViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "settingsViewModel" ],
        // Elements to bind to, e.g. #settings_plugin_drybox_sensor, #tab_plugin_drybox_sensor, ...
        elements: [ "#navbar_plugin_drybox_sensor"]
    });

});
