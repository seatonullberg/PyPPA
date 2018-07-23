from base_plugin import BasePlugin
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class WebBrowserPlugin(BasePlugin):

    def __init__(self):
        self.name = 'WebBrowserPlugin'
        # remember to place the single word spelling last to avoid 'best spelling' issue
        self.COMMAND_HOOK_DICT = {'search_google': ['search google for', 'search google', 'search for', 'google'],
                                  'search_netflix': ['search netflix for', 'search netflix', 'open netflix', 'netflix'],
                                  'search_youtube': ['search youtube for', 'search youtube', 'open youtube', 'youtube']}
        self.MODIFIERS = {'search_google': {},
                          'search_netflix': {},
                          'search_youtube': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name=self.name)

    def _generate_driver(self):
        CHROME_PROFILE_PATH = self.config_obj.environment_variables[self.name]['CHROME_PROFILE_PATH']
        # use the actual chromedriver binary at /usr/local/bin/chromedriver
        CHROMEDRIVER_PATH = self.config_obj.environment_variables[self.name]['CHROMEDRIVER_PATH']
        options = webdriver.ChromeOptions()
        options.add_argument("--user-data-dir={}".format(CHROME_PROFILE_PATH))
        options.add_argument("--disable-infobars")
        options.add_experimental_option('excludeSwitches', ['disable-component-update'])
        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                  chrome_options=options)
        return driver

    def search_google(self):
        driver = self._generate_driver()
        # send to the beta
        self.initialize_beta(name='google_search_beta',
                             cmd='search {}'.format(self.command_dict['premodifier']),
                             data=driver)

    def search_netflix(self):
        # set environment variables
        NETFLIX_EMAIL = self.config_obj.environment_variables[self.name]['NETFLIX_EMAIL']
        NETFLIX_PASSWORD = self.config_obj.environment_variables[self.name]['NETFLIX_PASSWORD']
        NETFLIX_USER = self.config_obj.environment_variables[self.name]['NETFLIX_USER']
        driver = self._generate_driver()
        driver.get('https://www.netflix.com/')
        # move to corner for easy cursor manipulation later
        driver.set_window_position(x=0, y=0)

        # sign in
        try:
            driver.find_element_by_link_text('Sign In').click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'login-body')))
            login_email_element = driver.find_element_by_id('email')
            login_password_element = driver.find_element_by_id('password')
            login_email_element.send_keys(NETFLIX_EMAIL)
            login_password_element.send_keys(NETFLIX_PASSWORD)
            driver.find_element_by_xpath("*//button[contains(text(),'Sign In')]").click()
        except selenium.common.exceptions.NoSuchElementException:
            print('already logged in')

        # select my profile
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'profile-icon')))
            driver.find_element_by_xpath("//span[text()='{}']".format(NETFLIX_USER)).click()
        except selenium.common.exceptions.NoSuchElementException:
            print('already selected account')

        # wait for search to be available
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'searchTab')))
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
