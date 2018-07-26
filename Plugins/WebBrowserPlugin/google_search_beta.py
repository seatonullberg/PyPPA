from base_beta import BaseBeta


# ~ambitious TODO: build another beta that reads html
# of the open links to attempt to create some generic control over all sites
# - organize a dict of links and their names
# - locate entry forms or search boxes
# - find main text to vocalize if requested
# -
class GoogleSearchBeta(BaseBeta):

    def __init__(self):
        self.COMMAND_HOOK_DICT = {'search': ['search for', 'search'],
                                  'exit_context': ['exit context'],
                                  'open': ['open', 'select']}
        self.MODIFIERS = {'search': {},
                          'exit_context': {},
                          'open': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='google_search_beta',
                         alpha_name='WebBrowserPlugin')

    def search(self):
        driver = self.DATA
        driver.get('https://www.google.com/search?q={}'.format(self.command_dict['premodifier']))

    def open(self):
        driver = self.DATA
        # iterate through the available links
        links = driver.find_elements_by_xpath("//h3[@class='r']/a")
        for link in links:
            href = link.get_attribute('href')
            text = link.text
            if self.command_dict['premodifier'] in text.lower():
                driver.get(href)
                break
