from base_plugin import BasePlugin
from multiprocessing import Process
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


class WebBrowserPlugin(BasePlugin):

    def __init__(self):
        # remember to place the single word spelling last to avoid 'best spelling' issue
        self.name = 'WebBrowserPlugin'
        # structure for now
        # search_google: do a google search for a given keyword or phrase
        # -- build Beta for enhanced audio control
        # search_netflix: open and login to netflix
        # -- build beta for enhanced audio control
        # search_youtube: do a youtube search to find videos related to a given keyword
        # -- build beta for enhanced audio support
        self.COMMAND_HOOK_DICT = {'search_google': ['search google for', 'search google', 'search for', 'google'],
                                  'search_netflix': ['search netflix for ', 'search netflix', 'open netflix'],
                                  'search_youtube': ['search youtube for', 'search youtube', 'open youtube']}
        self.MODIFIERS = {'search_google': {},
                          'search_netflix': {},
                          'search_youtube': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name=self.name)

    def _generate_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--user-data-dir=/home/seaton/.config/google-chrome/Default")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-fullscreen")
        driver = webdriver.Chrome(executable_path="/usr/lib/chromium-browser/chromedriver", chrome_options=options)
        return driver

    def search_google(self):
        driver = self._generate_driver()
        # send to the beta
        self.initialize_beta(name='google_search_beta',
                             cmd='search {}'.format(self.command_dict['premodifier']),
                             data=driver)

    def search_netflix(self):
        driver = self._generate_driver()
        # send to beta
        self.initialize_beta(name='netflix_search_beta',
                             cmd='search {}'.format(self.command_dict['premodifier']),
                             data=driver)

    def search_youtube(self):
        driver = self._generate_driver()
        # send to beta
        self.initialize_beta(name='youtube_search_beta',
                             cmd='search {}'.format(self.command_dict['premodifier']),
                             data=driver)

    def open_netflix(self):
        driver = self._generate_driver()
        driver.get('https://www.netflix.com/')
        # move to corner for easy cursor manipulation later
        driver.set_window_position(x=0, y=0)
        # sign in
        driver.find_element_by_link_text('Sign In').click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'login-body')))
        login_email_element = driver.find_element_by_id('email')
        login_password_element = driver.find_element_by_id('password')
        login_email_element.send_keys(NETFLIX_EMAIL)
        login_password_element.send_keys(NETFLIX_PASSWORD)
        driver.find_element_by_class_name('btn.login-button.btn-submit.btn-small').click()
        # select my profile
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'profile-icon')))
        driver.find_element_by_xpath("//span[text()='{}']".format(NETFLIX_USER)).click()
        # wait for search to be available
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'searchTab')))

        # initialize the beta plugin for greater control in separate process
        beta = NetflixSearchBeta('go back')
        nsb_thread = Process(target=beta.function_handler(args={'driver': driver}), name='netflix_search_beta')
        while beta.isBlocking:
            time.sleep(0.1)
        # after context is released from beta terminate its process
        nsb_thread.terminate()
        self.isBlocking = False

    def google_search(self, search_query):
        driver = webdriver.Firefox()
        driver.get('https://www.google.com/search?q='+search_query)
        #vocalize(Mannerisms('request_subsequent_command', None).final_response)
        #self.listener().pre_buffer = 10
        #sub_command = self.listener().listen_and_convert()
        #beta = GoogleSearchBeta(sub_command)
        # pass the driver for function handler to use
        #beta.function_handler(args={'driver': driver})
        self.isBlocking = False

    def youtube_search(self, search_query):
        # prepare search query
        search_query = search_query.replace(' ', '+')
        # establish driver
        profile = webdriver.FirefoxProfile(FIREFOX_PROFILE_PATH)
        driver = webdriver.Firefox(profile)
        driver.get('https://www.youtube.com/results?search_query=' + search_query)
        # wait for load and click first video
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'style-scope.ytd-video-renderer')))
        driver.find_element_by_xpath('//div/h3/a[@id="video-title"]').click()
        self.isBlocking = False
