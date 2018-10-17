from utils import web
from Plugins import base


# TODO: add pause/resume and viewer monitoring
class YoutubeSearchBeta(base.BetaPlugin):

    def __init__(self):
        self.command_hooks = {self.search: ['search for', 'search'],
                              self.play: ['play', 'open']}
        self.modifiers = {self.search: {},
                          self.play: {}}
        super().__init__(command_hooks=self.command_hooks,
                         modifiers=self.modifiers,
                         name='WebBrowserPlugin.YoutubeSearchBeta')
        self.webdriver = None

    def search(self):
        if self.webdriver is None:
            self.webdriver = web.WebDriver(self.configuration)
        self.webdriver.get('https://www.youtube.com/results?search_query={}'.format(self.command.premodifier))

    def play(self):
        if self.webdriver is None:
            self.webdriver = web.WebDriver(self.configuration)
        # iterate through available links
        links = self.webdriver.find_elements_by_id('video-title')
        for link in links:
            href = link.get_attribute('href')
            text = link.get_attribute('title')
            if self.command.premodifier in text.lower():
                self.webdriver.get(href)
                break
