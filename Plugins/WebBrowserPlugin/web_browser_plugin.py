import selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Plugins import base


class WebBrowserPlugin(base.Plugin):

    def __init__(self):
        self.name = 'WebBrowserPlugin'
        # remember to place the single word spelling last to avoid 'best spelling' issue
        self.command_hooks = {self.search_google: ['search google for', 'search google', 'search for', 'google'],
                              self.search_netflix: ['search netflix for', 'search netflix', 'open netflix', 'netflix'],
                              self.search_youtube: ['search youtube for', 'search youtube', 'open youtube', 'youtube']}
        self.modifiers = {self.search_google: {},
                          self.search_netflix: {},
                          self.search_youtube: {}}
        super().__init__(command_hooks=self.command_hooks,
                         modifiers=self.modifiers,
                         name=self.name)

    def search_google(self):
        # send to the beta
        cmd = 'search {}'.format(self.command.premodifier)
        self.request_plugin(plugin_name='WebBrowserPlugin.GoogleSearchBeta',
                            command_string=cmd)

    def search_netflix(self):
        # set environment variables
        netflix_email = self.request_environment_variable('NETFLIX_EMAIL')
        netflix_password = self.request_environment_variable('NETFLIX_PASSWORD')
        netflix_user = self.request_environment_variable('NETFLIX_USER')

        driver = self.webdriver
        driver.get('https://www.netflix.com/')
        # move to corner for easy cursor manipulation later
        driver.set_window_position(x=0, y=0)

        # sign in
        try:
            driver.find_element_by_link_text('Sign In').click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'login-body')))
            login_email_element = driver.find_element_by_id('id_userLoginId')
            login_password_element = driver.find_element_by_id('id_password')
            login_email_element.send_keys(netflix_email)
            login_password_element.send_keys(netflix_password)
            driver.find_element_by_xpath("*//button[contains(text(),'Sign In')]").click()
        except selenium.common.exceptions.NoSuchElementException:
            print('already logged in')

        # select my profile
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'profile-icon')))
            driver.find_element_by_xpath("//span[text()='{}']".format(netflix_user)).click()
        except selenium.common.exceptions.NoSuchElementException:
            print('already selected account')

        # wait for search to be available
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'searchTab')))
        # send to beta
        cmd = 'search {}'.format(self.command.premodifier)
        self.request_plugin(plugin_name='WebBrowserPlugin.NetflixSearchBeta', command_string=cmd)

    def search_youtube(self):
        cmd = 'search {}'.format(self.command.premodifier)
        # send to beta
        self.request_plugin(plugin_name='WebBrowserPlugin.YoutubeSearchBeta', command_string=cmd)
