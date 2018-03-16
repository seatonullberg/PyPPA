from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Speaker import vocalize
from floating_listener import listen_and_convert
from mannerisms import Mannerisms
from Plugins.WebBrowserPlugin.google_search_beta import GoogleSearchBeta
from api_config import NETFLIX_EMAIL, NETFLIX_PASSWORD, NETFLIX_USER
import time
'''
TODO:
- add 'and' modifier
- ask for further commands to determine sleep/active status
- add youtube_search amd stack_exchange_search
'''


class PyPPA_WebBrowserPlugin(object):

    def __init__(self, command):
        self.command = command
        # remember to place the single word spelling last to avoid 'best spelling' issue
        self.COMMAND_HOOK_DICT = {'open': ['open up', 'open it', 'open'],
                                  'search_google': ['search google for', 'search for', 'google'],
                                  'search_netflix': ['search netflix for', 'search netflix', 'netflix']}
        # use these functions to clarify what might be spelled incorrectly
        self.FUNCTION_KEY_DICT = {'canvas': ['canvas', 'e learning']}

    def function_handler(self, command_hook, spelling):
        '''
        Function required to map user commands with their final function
        :return: None
        '''
        if command_hook == 'search_google':
            # prepare for a google search
            search_query = self.command.replace(spelling, '')
            split_query = list(search_query.split(' '))
            search_query = '+'.join(split_query)
            self.google_search(search_query)
        elif command_hook == 'search_netflix':
            # prepare for a netflix search
            search_query = self.command.replace(spelling, '')
            self.netflix_search(search_query)
        else:
            # the open hook is being used

            # check for UFL canvas
            for variations in self.FUNCTION_KEY_DICT['canvas']:
                if variations in self.command:
                    self.open_canvas()
                    return
            # attempt to find correct website
            # improve with more robust command screening
            self.catch_all(spelling)

    def update_database(self):
        pass

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

    def open_canvas(self):
        driver = webdriver.Firefox()
        driver.get(r'https://ufl.instructure.com/')

    def google_search(self, search_query):
        driver = webdriver.Firefox()
        driver.get('https://www.google.com/search?q='+search_query)
        vocalize(Mannerisms('request_subsequent_command', None).final_response)
        sub_command = listen_and_convert()
        beta = GoogleSearchBeta(sub_command, driver)
        beta.function_handler()

    def netflix_search(self, search_query):
        driver = webdriver.Firefox()
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

        # go to search bar
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'searchTab')))
        if search_query != '':
            driver.find_element_by_class_name('searchTab').click()
            search_entry = driver.find_element_by_xpath('//div/div/input')
            search_entry.send_keys(search_query)
            # wait for results and click the first result for now
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'suggestionRailContainer')))
            try:
                driver.find_element_by_xpath('//div[@id="title-card-0-0"]').click()
            except exceptions.ElementClickInterceptedException:
                driver.find_element_by_xpath('//div[@class="ratio-16x9 pulsate-transparent"]').click()
