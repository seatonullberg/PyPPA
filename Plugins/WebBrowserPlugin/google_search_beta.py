from Plugins import base
from utils import web

# ~ambitious TODO: build another beta that reads html
# of the open links to attempt to create some generic control over all sites
# - organize a dict of links and their names
# - locate entry forms or search boxes
# - find main text to vocalize if requested
# -


class GoogleSearchBeta(base.BetaPlugin):

    def __init__(self):
        self.command_hooks = {self.search: ['search for', 'search'],
                              self.open: ['open', 'select']}
        self.modifiers = {self.search: {},
                          self.open: {}}
        super().__init__(command_hooks=self.command_hooks,
                         modifiers=self.modifiers,
                         name='WebBrowserPlugin.GoogleSearchBeta')
        self.webdriver = None

    def search(self):
        if self.webdriver is None:
            self.webdriver = web.WebDriver(self.configuration)
        self.webdriver.get('https://www.google.com/search?q={}'.format(self.command.premodifier))

    def open(self):
        if self.webdriver is None:
            self.webdriver = web.WebDriver(self.configuration)
        # iterate through the available links
        links = self.webdriver.find_elements_by_xpath("//h3[@class='r']/a")
        for link in links:
            href = link.get_attribute('href')
            text = link.text
            if self.command.premodifier in text.lower():
                self.webdriver.get(href)
                break
