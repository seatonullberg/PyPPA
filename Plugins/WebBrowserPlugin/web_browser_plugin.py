from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from Speaker import vocalize
from Plugins.base_plugin import BasePlugin
from mannerisms import Mannerisms
from Plugins.WebBrowserPlugin.google_search_beta import GoogleSearchBeta
from private_config import NETFLIX_EMAIL, NETFLIX_PASSWORD, NETFLIX_USER, FIREFOX_PROFILE_PATH


# TODO: Make the netflix function a beta and have it hold attention for full site navigation by voice
class PyPPA_WebBrowserPlugin(BasePlugin):

    def __init__(self, command):
        # remember to place the single word spelling last to avoid 'best spelling' issue
        self.COMMAND_HOOK_DICT = {'open': ['open up', 'open it', 'open'],
                                  'search_google': ['search google for', 'search for', 'google'],
                                  'search_netflix': ['search netflix for', 'search netflix', 'netflix'],
                                  'search_youtube': ['search youtube for', 'search youtube', 'youtube']}
        self.MODIFIERS = {'open': {'canvas': ['canvas', 'e learning']},
                          'search_google': {},
                          'search_netflix': {},
                          'search_youtube': {}
                          }
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None):
        '''
        Function required to map user commands with their final function
        :return: None
        '''
        if self.command_dict['command_hook'] == 'search_google':
            # prepare for a google search
            self.google_search(self.command_dict['premodifier'])
        elif self.command_dict['command_hook'] == 'search_netflix':
            # prepare for a netflix search
            self.netflix_search(self.command_dict['premodifier'])
        elif self.command_dict['command_hook'] == 'search_youtube':
            # prepare youtube search
            self.youtube_search(self.command_dict['premodifier'])
        else:
            # the open hook is being used
            if self.command_dict['modifier'] == 'canvas':
                self.open_canvas()
            else:
                self.catch_all(self.command_dict['premodifier'])

    '''
    --------------------------------------------------------------------------------------------------------
    Begin Module Functions
    --------------------------------------------------------------------------------------------------------
    '''

    def catch_all(self, spelling):
        self.command = self.command.replace(spelling, '')
        command_no_spaces = self.command.replace(' ', '')
        driver = webdriver.Firefox()
        driver.get(r'http://www.'+command_no_spaces+'.com/')
        self.isBlocking = False

    def open_canvas(self):
        driver = webdriver.Firefox()
        driver.get(r'https://ufl.instructure.com/')
        self.isBlocking = False

    def google_search(self, search_query):
        driver = webdriver.Firefox()
        driver.get('https://www.google.com/search?q='+search_query)
        vocalize(Mannerisms('request_subsequent_command', None).final_response)
        sub_command = self.listener().listen_and_convert()
        beta = GoogleSearchBeta(sub_command, driver)
        beta.function_handler()
        self.isBlocking = False

    def netflix_search(self, search_query):
        # format the search url
        search_query = search_query.replace(' ', '%20')

        profile = webdriver.FirefoxProfile(FIREFOX_PROFILE_PATH)
        driver = webdriver.Firefox(profile)
        driver.get('https://www.netflix.com/')
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

        # wait for search and navigate to search url
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'searchTab')))
        if search_query != '':
            driver.get('https://www.netflix.com/search?q='+search_query)
            # wait for results and click the first result for now
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'suggestionRailContainer')))
            title_card = driver.find_element_by_xpath('//div[@id="title-card-0-0"]')
            ActionChains(driver).move_to_element(title_card).perform()
            play_link = driver.find_element_by_xpath('//div[@id="title-card-0-0"]/div/a')
            play_link = play_link.get_attribute('href')
            driver.get(play_link)
            # go full screen
            driver.set_window_size(1920, 1080)
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
