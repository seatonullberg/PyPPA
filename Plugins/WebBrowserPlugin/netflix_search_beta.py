import selenium
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pyautogui
from threading import Thread
from queue import Queue

from Plugins.WebBrowserPlugin.web_browser_plugin import WebBrowserPlugin


class NetflixSearchBeta(WebBrowserPlugin):

    def __init__(self):
        super().__init__()
        self.name = 'WebBrowserPlugin.NetflixSearchBeta'
        self.command_hooks = {self.search: ['search for', 'search'],
                              self.play: ['play'],
                              self.pause: ['pause', 'resume', 'start', 'stop']}
        self.modifiers = {self.search: {},
                          self.play: {'position': ['position']},
                          self.pause: {}}

        self.status = None
        self.monitor_queue = Queue()
        self.monitor_thread = None
        self.webdriver = None
        self.logged_in = False

    def search(self):
        self._check_webdriver()
        if not self.logged_in:
            self._login()
        self.webdriver.get('https://www.netflix.com/search?q={}'.format(self.command.premodifier))
        self.status = 'search'

    def play(self):
        self._check_webdriver()
        if not self.logged_in:
            self._login()
        # use row, column position notation to specify a show tile frm search
        if self.command.modifier == 'position':
            try:
                row, col = self.command.postmodifier.split(' ')
                print(row, col)
            except ValueError:
                return
        # do a search for the name and open the first result
        else:
            self.webdriver.get('https://www.netflix.com/search?q={}'.format(self.command.premodifier))
            # click the first panel
            title_card = self.webdriver.find_element_by_xpath('//div[@id="title-card-0-0"]')
            ActionChains(self.webdriver).move_to_element(title_card).perform()
            play_link = self.webdriver.find_element_by_xpath('//div[@id="title-card-0-0"]/div/a')
            play_link = play_link.get_attribute('href')
            self.webdriver.get(play_link)
            # go full screen
            self.webdriver.maximize_window()
            # Press spacebar to start right away
            self.pause()
        self.status = 'play'
        # spawn a thread to monitor the viewers
        if self.monitor_thread is None:
            self.monitor_thread = Thread(target=self._monitor_viewers, args=(self.monitor_queue,))
            self.monitor_thread.start()

    def pause(self):
        # click on netflix page in blank location to ensure the signal works
        pyautogui.click(x=300, y=300)
        # now send spacebar signal to pause
        ActionChains(self.webdriver).key_down(Keys.SPACE).key_up(Keys.SPACE).perform()

    def annotate(self):
        # use when interrogative is done
        raise NotImplementedError()

    def exit_context(self):
        if self.webdriver is not None:
            self.webdriver.quit()
        self.logged_in = False
        self.monitor_queue.put('quit')
        self.request_plugin('WebBrowserPlugin', '')

    def _login(self):
        self._check_webdriver()

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
        self.logged_in = True

    def _monitor_viewers(self, q):
        initial_viewer = None
        candidates = {}
        exit_count = 0
        while True:
            # check for quit signal
            if not q.empty():
                if q.get() == 'quit':
                    break
            # get frame data from cache
            frame_data = self.from_cache('WatcherPlugin')
            if frame_data is None:
                continue
            face_names = [d['name'] for d in frame_data]

            # set the initial viewer
            if initial_viewer is None:
                for name in face_names:
                    if name in candidates:
                        candidates[name] += 1
                    else:
                        candidates[name] = 0
                for k, v in candidates.items():
                    # if a candidate has 25 counts they become the initial user
                    if v > 25:
                        initial_viewer = k
                        print(initial_viewer)
                        break
            # monitor presence of initial viewer
            else:
                if initial_viewer not in face_names:
                    exit_count += 1
                else:
                    exit_count = 0
                # after a 25 frame exit reset the counters and pause netflix
                if exit_count > 25:
                    candidates = {}
                    exit_count = 0
                    initial_viewer = None
                    self.pause()

