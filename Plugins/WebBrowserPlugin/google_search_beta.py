from Plugins.WebBrowserPlugin.web_browser_plugin import WebBrowserPlugin


class GoogleSearchBeta(WebBrowserPlugin):

    def __init__(self):
        super().__init__()
        # override base commands
        self.command_hooks = {self.search: ['search for', 'search'],
                              self.open: ['open', 'select']}
        self.modifiers = {self.search: {},
                          self.open: {}}
        self.name = 'WebBrowserPlugin.GoogleSearchBeta'
        self.webdriver = None

    def search(self):
        self._check_webdriver()
        self.webdriver.get('https://www.google.com/search?q={}'.format(self.command.premodifier))

    def open(self):
        self._check_webdriver()
        # iterate through the available links
        links = self.webdriver.find_elements_by_xpath("//h3[@class='r']/a")
        for link in links:
            href = link.get_attribute('href')
            text = link.text
            if self.command.premodifier in text.lower():
                self.webdriver.get(href)
                break
