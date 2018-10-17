from Plugins.WebBrowserPlugin.web_browser_plugin import WebBrowserPlugin


# TODO: add pause/resume and viewer monitoring
class YoutubeSearchBeta(WebBrowserPlugin):

    def __init__(self):
        super().__init__()
        # replace the inherited values
        self.name = 'WebBrowserPlugin.YoutubeSearchBeta'
        self.command_hooks = {self.search: ['search for', 'search'],
                              self.play: ['play', 'open']}
        self.modifiers = {self.search: {},
                          self.play: {}}
        self.webdriver = None

    def search(self):
        self._check_webdriver()
        self.webdriver.get('https://www.youtube.com/results?search_query={}'.format(self.command.premodifier))

    def play(self):
        self._check_webdriver()
        # iterate through available links
        links = self.webdriver.find_elements_by_id('video-title')
        for link in links:
            href = link.get_attribute('href')
            text = link.get_attribute('title')
            if self.command.premodifier in text.lower():
                self.webdriver.get(href)
                break
