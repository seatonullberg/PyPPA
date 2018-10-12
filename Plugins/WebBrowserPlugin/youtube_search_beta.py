from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
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

    def search(self):
        self.webdriver.get('https://www.youtube.com/results?search_query={}'.format(self.command.premodifier))

    def play(self):
        # iterate through available links
        links = self.webdriver.find_elements_by_id('video-title')
        for link in links:
            href = link.get_attribute('href')
            text = link.get_attribute('title')
            if self.command.premodifier in text.lower():
                self.webdriver.get(href)
                break
