from Plugins.WebBrowserPlugin.web_browser_plugin import PyPPA_WebBrowserPlugin
from Plugins.TeacherPlugin.teacher_plugin import PyPPA_TeacherPlugin
from Plugins.WeatherPlugin.weather_plugin import PyPPA_WeatherPlugin
from Plugins.NewsPlugin.news_plugin import PyPPA_NewsPlugin

LISTENER_ENERGY_THRESHOLD = 3000

# include all desired module classes
PLUGIN_LIST = [PyPPA_WebBrowserPlugin, PyPPA_WeatherPlugin, PyPPA_TeacherPlugin, PyPPA_NewsPlugin]
