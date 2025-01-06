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
        self.dryboxTimeSpan = ko.observable("7 days");       
        //console.log("DRYBOX SETTINGS!!!!!");
        //console.log(self.settings);
        //console.log(self.settingsViewModel);

        self.onDataUpdaterPluginMessage = function (plugin, data) {
          //console.log("Drybox sensor data update : " + plugin);
          //console.log(data);
          //for (d in data) {
          //  console.log(d + " : " + data[d]);
	        //}
          if (plugin != "drybox_sensor") {
              return;
          }
	        if (data.temp == -1 && data.humid == -1) {
	        // Connection error. 
            $('#drybox-temp').html("Not Connected").addClass("drybox_error");
            $('#drybox-humid').hide();
          }
          else if (data.temp == -2 && data.humid == -2) {
            // Data Timeout error. 
              $('#drybox-temp').html("Data Timeout").addClass("drybox_error");
              $('#drybox-humid').hide();
          }  
          else {
            $('#drybox-humid').show();
            if (data.temp) {
              $('#drybox-temp').html(_.sprintf(":%.1f&deg;C", data.temp)).removeClass("drybox_error drybox_warn");
              if (data.temp > self.settings.settings.plugins.drybox_sensor.temp_error()) {
                $('#drybox-temp').addClass("drybox_error");
              }
              else if (data.temp > self.settings.settings.plugins.drybox_sensor.temp_warn()) {
                $('#drybox-temp').addClass("drybox_warn");
              }
              
            }
            if (data.humid) {
              $('#drybox-humid').html(_.sprintf("%.1f%%", data.humid)).removeClass("drybox_error drybox_warn");
              if (data.humid > self.settings.settings.plugins.drybox_sensor.humid_error()) {
                $('#drybox-humid').addClass("drybox_error");
              }
              else if (data.humid > self.settings.settings.plugins.drybox_sensor.humid_warn()) {
                $('#drybox-humid').addClass("drybox_warn");
              }
              
            }
          }


        }
        
        self.printTextHistory = function(data) {
            
            html = "<ul class='drybox-histlist'>";
            var count = 0;
            for (h in self.tdata) {
              var d = new Date(self.tdata[h]['ts']*1000);
                
              html += "<li>" + d.toLocaleString() + "  ";
              tclass = "";
              if (self.tdata[h]['temp'] > parseInt(self.settings.settings.plugins.drybox_sensor.temp_error())) {
                tclass = "drybox_error";
              }
              else if (self.tdata[h]['temp'] > parseInt(self.settings.settings.plugins.drybox_sensor.temp_warn())) {
                tclass = "drybox_warn"; 
              }
              
              html += "<b class='" + tclass + "'>" + _.sprintf("%3.1f&deg;C", self.tdata[h]['temp']) + "</b>";
              hclass = "";
              if (self.tdata[h]['humid'] > self.settings.settings.plugins.drybox_sensor.humid_error()) {
                hclass = "drybox_error";
              }
              else if (self.tdata[h]['humid'] > self.settings.settings.plugins.drybox_sensor.humid_warn()) {
                hclass = "drybox_warn";
              }
              html += "<b class='" + hclass + "'>" + _.sprintf("%3.1f%%", self.tdata[h]['humid']) + "</b></li>\n";
            }
            html += "</ul>"
            $('#drybox-history').html(html);
          
        }
       

        self.onBeforeBinding = function() {
          //self.settings = self.global_settings.settings.plugins.drybox_sensor;
          console.log("DRYBOX: On Before Binding : " + self.global_settings);
        }
        
	self.onHideDryBox = function() {
		$('#drybox-history-div').hide();
	}
	
  self.onShowDryBox = function() {
    if (!$('#drybox-history-div').is(':visible')) {
		  $('#drybox-history-div').show();
	    self.dryboxTimeSpanChecked();
    }
	}

	self.showDryBoxHistText = function(event) {
	   event.stopPropagation();
	   $('#drybox-history-scroll').toggle();
	   $('#drybox-graph').toggle();
	   $('#drybox-graph-legend').toggle();
     
     self.dryboxTimeSpanChecked(); 
	}

    self.dryboxGetData = function(tspan, count, callback) {
        $.ajax({
            url:         "/api/plugin/drybox_sensor",
            type:        "POST",
            contentType: "application/json",
            dataType:    "json",
            async:       false,
            headers:     {"X-Api-Key": UI_API_KEY},
            data:        JSON.stringify({ "command": "graph_tspan", "tspan": tspan, "count":count }),
            complete: function (data) {
                //console.log("POSt completed: ");
                //console.log(data.responseJSON);
                self.tdata=data.responseJSON;
                callback();
            }
	   });
    } 

	self.dryboxTimeSpanChecked = function() {
    var dbts = $('input[name="drybox-timespan"]:checked');
	  var value = dbts[0].value; 
    //console.log("Timespan = " + value + " from element");
	  if ($('#drybox-history-scroll').is(':visible')) {
      // We are showing text
      self.dryboxGetData(value, 50, self.printTextHistory); 
    }
    else {
	    var canvas = document.getElementById("drybox-graph");
      self.dryboxGetData(value, canvas.width, self.draw_drybox_graph);
    }
	}
		
	self.draw_drybox_graph = function(){
        if (self.tdata && self.tdata.length == 0) {
          console.log("No temp/humid data, not drawing graph"); 
          return;
        }
	    var canvas = document.getElementById("drybox-graph");
	    var cdiv = document.getElementById("drybox-history-div");
	    canvas.width = cdiv.offsetWidth*.95;
	    canvas.height = cdiv.offsetHeight*0.8;
	    var context = canvas.getContext("2d");
	    
	    console.log("DRYBOX Canvas size: " + canvas.width + "x" + canvas.height);
	    dp = []
	    for (td in self.tdata) {
		dp.push(self.tdata[td]['humid']);
		dp.push(self.tdata[td]['temp']);
	    }
	    var maxv = Math.max(...dp);
	    var minv = Math.min(...dp);
	    var MAX_SCALE = Math.floor(maxv+(5-(maxv%5)));
	    var MIN_SCALE = Math.floor(minv-(minv%5));
	    
	    var LABEL_WIDTH=60;
	    var LABEL_HEIGHT=15;

	    var graph_height = canvas.height - LABEL_HEIGHT - 5;
	    //clear the canvas
	    context.clearRect(0, 0, canvas.width, canvas.height);
	    context.moveTo(0, 0);
	    
	    //draw the graph line for humid data (blue)
	    context.beginPath();
	    context.lineWidth = 1;
	    context.strokeStyle = "#0000ff";
	    context.moveTo(0, canvas.height - ((graph_height * (self.tdata[0]['humid']-MIN_SCALE)) / (MAX_SCALE-MIN_SCALE))-LABEL_HEIGHT);
	    for(var i = 0; i < self.tdata.length; i++){
		context.lineTo((i+1) * ((canvas.width - LABEL_WIDTH) / self.tdata.length), canvas.height - ((graph_height * (self.tdata[i]['humid']-MIN_SCALE)) / (MAX_SCALE-MIN_SCALE)) - LABEL_HEIGHT);
	    }
	    context.stroke();

	    //fill humid data
	    context.fillStyle = "rgba(0, 0, 255, 0.1)";
	    context.lineTo(canvas.width - LABEL_WIDTH-1, graph_height);
	    context.lineTo(1, graph_height);
	    context.closePath();
	    context.fill();

	    //draw the graph line for temp data
	    context.beginPath();
	    context.lineWidth = 1;
	    context.strokeStyle = "#ff0000";
	    context.moveTo(0, canvas.height - ((graph_height * (self.tdata[0]['temp']-MIN_SCALE)) / (MAX_SCALE-MIN_SCALE)) - LABEL_HEIGHT);
	    for(i = 0; i < self.tdata.length; i++){
		context.lineTo((i+1) * ((canvas.width - LABEL_WIDTH) / self.tdata.length), canvas.height - ((graph_height * (self.tdata[i]['temp']-MIN_SCALE)) / (MAX_SCALE-MIN_SCALE)) - LABEL_HEIGHT );
	    }
	    context.stroke();
	    //fill data2
	    context.fillStyle = "rgba(255, 0, 0, 0.1)";
	    context.lineTo(canvas.width - LABEL_WIDTH - 1, graph_height);
	    context.lineTo(1, graph_height);
	    context.closePath();
	    context.fill(); 
	    

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

      var lastmark = self.tdata.length-1;
      var gtspan = self.tdata[lastmark]['ts'].valueOf()-self.tdata[0]['ts'].valueOf();
	    
      var num_marks = 10;
      var hourspan = gtspan/60/60;
      var hours = [1,3,6,12,24]
      var hour_index = 0;
      while (num_marks > 7) {
        num_marks = Math.round(hourspan/hours[hour_index++]);
      }
      hourspan = hours[hour_index];
      var marks = Array(num_marks).fill(-1);
      var markindex = 0;
      while (lastmark > self.tdata.length*((num_marks-markindex-2)/num_marks) && lastmark > 0) {
        var lastmarkd = new Date(self.tdata[lastmark]['ts'].valueOf()*1000);
        var nextmarkd = new Date(self.tdata[lastmark-1]['ts'].valueOf()*1000);
        if (lastmarkd.getMinutes() < nextmarkd.getMinutes() && lastmarkd.getHours()%hourspan==0) {
          console.log(markindex, lastmarkd, nextmarkd);
          marks[markindex] = lastmark;
          markindex+=1;
          lastmark -= 1;
          if (markindex >= marks.length) {
            console.log("all marks done", marks);
            break;
          }
        }
        lastmark -= 1;
      }
        
      console.log("Marks :", marks);
      for (let mark = 0; mark += 1 ; mark <= num_marks) {
        var tindex = marks[mark];
        var ts = self.tdata[tindex]['ts'];
        console.log(mark + " : " + tindex + " : " + ts);
        var d = new Date(ts*1000);
        context.moveTo((canvas.width-LABEL_WIDTH)/self.tdata.length * tindex, 0);
        context.lineTo((canvas.width-LABEL_WIDTH)/self.tdata.length * tindex, graph_height+5);
        context.font = LABEL_HEIGHT + "px serif";
        context.fillStyle = "black";
        var dstr = d.getDate() + "/" + (d.getMonth()+1) + " " + d.getHours() + ":" 
		      + (d.getMinutes() > 9 ? d.getMinutes() : "0" + d.getMinutes());   
		    //var dstr = "-1 day"; 
		    context.fillText(dstr,((canvas.width-LABEL_WIDTH)/self.tdata.length * tindex) - LABEL_WIDTH/2, canvas.height);	 
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

