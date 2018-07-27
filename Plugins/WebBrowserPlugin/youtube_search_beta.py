from base_beta import BaseBeta
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


# TODO: add pause/resume and viewer monitoring
class YoutubeSearchBeta(BaseBeta):

    def __init__(self):
        self.COMMAND_HOOK_DICT = {'search': ['search for', 'search'],
                                  'play': ['play', 'open']}
        self.MODIFIERS = {'search': {},
                          'play': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='youtube_search_beta',
                         alpha_name='WebBrowserPlugin')

    def search(self):
        driver = self.DATA
        driver.get('https://www.youtube.com/results?search_query={}'.format(self.command_dict['premodifier']))

    def play(self):
        driver = self.DATA
        # iterate through available links
        links = driver.find_elements_by_id('video-title')
        for link in links:
            href = link.get_attribute('href')
            text = link.get_attribute('title')
            if self.command_dict['premodifier'] in text.lower():
                driver.get(href)
                break

    def exit_context(self, cmd=None):
        self.DATA.quit()
        super().exit_context(cmd)
