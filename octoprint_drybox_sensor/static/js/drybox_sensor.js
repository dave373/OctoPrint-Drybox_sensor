/*
 * View model for OctoPrint-Drybox_sensor
 *
 * Author: David Haddon
 * License: AGPLv3
 */
$(function() {
    
    function Drybox_sensorViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        self.settings = parameters[0];
        self.settingsViewModel = parameters[1];
        
        self.dryboxTemp = ko.observable();
        self.dryboxHumid = ko.observable();
        self.dryboxHistory = ko.observable();
        
        //console.log("DRYBOX SETTINGS!!!!!");
        //console.log(self.settings);
        
        self.onDataUpdaterPluginMessage = function (plugin, data) {
          //console.log("Drybox sensor data update");
          /*for (d in data) {
            console.log(d + " : " + data[d]);
          }
          */
          if (plugin != "drybox_sensor") {
              return;
          }

          if (data.temp) {
            $('#drybox-temp').html(_.sprintf(":%.1f&deg;C", data.temp));
          }
          if (data.humid) {
            $('#drybox-humid').html(_.sprintf("%.1f%%", data.humid)).removeClass("drybox_error drybox_warn");
            if (data.humid > self.settings.settings.plugins.drybox_sensor.humid_warn()) {
              $('#drybox-humid').addClass("drybox_warn");
            }
            if (data.humid > self.settings.settings.plugins.drybox_sensor.humid_error()) {
              $('#drybox-humid').addClass("drybox_error");
            }
          }
          if (data.history) {
            html = "<ul class='drybox-histlist'>";
            for (h in data.history) {
              var d = new Date(data.history[h]['ts']*1000)
              html += "<li>" + d.toLocaleString() + "  " + _.sprintf("%3.1f%%", data.history[h]['temp']) + "  " + _.sprintf("%3.1f%%", data.history[h]['humid']) + "</li>";
            }
            html += "</ul>"
            $('#drybox-history').html(html);
          }
        }

        self.onBeforeBinding = function() {
          self.settings = self.global_settings.settings.plugins.drybox_sensor;
          
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
        elements: [ "#drybox-temp", "#drybox-humid"]
    });
});
