import octoprint.plugin
from octoprint.util import RepeatedTimer
from .libs.dbserial import DBSerial

class DryBoxSensorPlugin(octoprint.plugin.StartupPlugin, 
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.AssetPlugin):
   
    def on_after_startup(self):
        self._logger.info("Drybox sensor using port:%s" %self._settings.get(["port"]))
        self.serialNode = DBSerial(self._settings.get(["port"]),self)
        self.serialNode.start()
        self._logger.info("Finished startup")

    def on_shutdown(self):
        self.serialNode.stop()

    
    def get_settings_defaults(self):
        return dict(port="debug",
                    humid_warn=25,
                    humid_error=30,
                    hist_length=10,
                    hist_delay="24h"
                    )
    
    def on_settings_save(self, data):
        diff = super(DryBoxSensorPlugin, self).on_settings_save(data)
        self._logger.info("Settings saved.. data: %s" %data)
        if "port" in data:
            self.serialNode.stop()
            self.serialNode = self.serialNode = DBSerial(data["port"],self)
            self.serialNode.start()
            self._logger.info("Serial reader restarted with new port")
        if "hist_length" in data:
            self.serialNode.hist_length = int(data["hist_length"])
        if "hist_delay" in data:
            if "m" in data["hist_delay"]:
                self.serialNode.hist_delay = int(data["hist_delay"].strip('m')) * 60
            elif "h" in data["hist_delay"]:
                self.serialNode.hist_delay = int(data["hist_delay"].strip('m')) * 3600
            else:
                self.serialNode.hist_delay = int(data["hist_delay"].strip('s'))
            
        self._plugin_manager.send_plugin_message(self._identifier, dict())
        return diff

    def get_template_vars(self):
        return dict(port=self._settings.get(["port"]),
                    humid_warn=self._settings.get(["humid_warn"]),
                    humid_error=self._settings.get(['humid_error'])
                    )
        
    
    def get_template_configs(self):
        return [
          dict(type="navbar", custom_bindings=False),
          dict(type="settings", custom_bindings=False)
        ]

    def get_assets(self):
        self._logger.info("Get Assets accessed")
        return dict(
          js=["js/drybox_sensor.js"],
          css=["css/drybox_sensor.css"]
        )


__plugin_name__ = "DryBox Sensor"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = DryBoxSensorPlugin()

