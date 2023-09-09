import octoprint.plugin

class DryBoxSensorPlugin(octoprint.plugin.StartupPlugin, 
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.SettingsPlugin):
    def on_after_startup(self):
        self._logger.info("Drybox sensor using port:%s" %self._settings.get(["port"]))
      
    def get_settings_defaults(self):
        return dict(port="/dev/ttyUSB1")

    def get_template_vars(self):
        return dict(port=self._settings.get(["port"]))

__plugin_name__ = "DryBox Sensor"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = DryBoxSensorPlugin()

