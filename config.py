# standard plugins
from Plugins.WebBrowserPlugin.web_browser_plugin import PyPPA_WebBrowserPlugin
from Plugins.TeacherPlugin.teacher_plugin import PyPPA_TeacherPlugin
from Plugins.WeatherPlugin.weather_plugin import PyPPA_WeatherPlugin
from Plugins.NewsPlugin.news_plugin import PyPPA_NewsPlugin
from Plugins.ChatPlugin.chat_plugin import PyPPA_ChatPlugin
from Plugins.WatcherPlugin.watcher_plugin import PyPPA_WatcherPlugin
# background tasks
from BackgroundTasks.Reddit.reddit_bot import RedditBot
from BackgroundTasks.Wikipedia.wiki_articles import WikiCollector

# include all desired module classes
PLUGIN_LIST = [PyPPA_WebBrowserPlugin, PyPPA_WeatherPlugin, PyPPA_TeacherPlugin, PyPPA_NewsPlugin, PyPPA_ChatPlugin,
               PyPPA_WatcherPlugin]

# include all desired background tasks
BACKGROUND_TASKS = [RedditBot, WikiCollector]
