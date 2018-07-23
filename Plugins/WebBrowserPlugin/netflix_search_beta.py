from base_beta import BaseBeta
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pyautogui


class NetflixSearchBeta(BaseBeta):

    def __init__(self):
        self.COMMAND_HOOK_DICT = {'search': ['search for', 'search'],
                                  'play': ['play'],
                                  'pause': ['pause', 'resume', 'start', 'stop']}
        self.MODIFIERS = {'search': {},
                          'play': {'position': ['position']},
                          'pause': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='netflix_search_beta',
                         alpha_name='WebBrowserPlugin')
        self.status = None

    def search(self):
        driver = self.DATA
        driver.get('https://www.netflix.com/search?q={}'.format(self.command_dict['premodifier']))
        self.status = 'search'

    # TODO
    def play(self):
        driver = self.DATA
        # use row, column position notation to specify a show tile frm search
        if self.command_dict['modifier'] == 'position':
            try:
                row, col = self.command_dict['postmodifier'].split(' ')
                print(row, col)
            except ValueError:
                return
        # do a search for the name and open the first result
        else:
            driver.get('https://www.netflix.com/search?q={}'.format(self.command_dict['premodifier']))
            # click the first panel
            title_card = driver.find_element_by_xpath('//div[@id="title-card-0-0"]')
            ActionChains(driver).move_to_element(title_card).perform()
            play_link = driver.find_element_by_xpath('//div[@id="title-card-0-0"]/div/a')
            play_link = play_link.get_attribute('href')
            driver.get(play_link)
            # go full screen
            driver.maximize_window()
            # Press spacebar to start right away
            self.pause()

    def pause(self):
        driver = self.DATA
        # click on netflix page in blank location to ensure the signal works
        pyautogui.click(x=300, y=300)
        # now send spacebar signal to pause
        ActionChains(driver).key_down(Keys.SPACE).key_up(Keys.SPACE).perform()

    def annotate(self):
        # use when interrogative is done
        raise NotImplementedError()

    def exit_context(self, cmd=None):
        self.DATA.quit()
        super().exit_context(cmd)

