from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from threading import Thread
import threading
import pickle
import os
import pyautogui

from base_plugin import BasePlugin
from private_config import DATA_DIR


class NetflixSearchBeta(BasePlugin):

    def __init__(self):
        self.driver = None
        self.isPaused = False
        self.last_url = 'https://www.netflix.com/browse'
        self.COMMAND_HOOK_DICT = {'search_for': ['search for', 'look for', 'find'],
                                  'play': ['play', 'start'],
                                  'pause': ['pause'],
                                  'go_back': ['go back to the menu', 'go back to menu', 'go back'],
                                  'release_context': ['release context', 'escape context']
                                  }
        self.MODIFIERS = {'search_for': {},
                          'play': {'number': ['result number', 'number', 'result']},    # select by row order
                          'pause': {},
                          'go_back': {},
                          'release_context': {}
                          }
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='netlifx_search_beta')

    def function_handler(self, args=None):
        # get driver in args
        self.driver = args['driver']

        # TODO: build this into base class as default method of determining function call
        hook_func_dict = {'search_for': self.search_for,
                          'play': self.play,
                          'pause': self.pause_unpause,
                          'go_back': self.go_back,
                          'release_context': self.release_context}
        if self.command_dict['command_hook'] in hook_func_dict:
            hook_func_dict[self.command_dict['command_hook']]()

        self.lock_context(args={'driver': self.driver}, pre_buffer=20)

    def search_for(self):
        # search no longer defaults to playing the first listing
        # must specify what to play with 'play' command
        query = self.command_dict['premodifier'].replace(' ', '%20')
        self.driver.get('https://www.netflix.com/search?q={}'.format(query))
        # wait for results to load before returning
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'suggestionRailContainer')))
        # store last url for go_back
        self.last_url = 'https://www.netflix.com/search?q={}'.format(query)

    def play(self):
        if self.command_dict['modifier'] == 'number':
            position = self.command_dict['postmodifier']
        else:
            # navigate to the search page of the query and play first listing
            # less accurate than specifying position
            self.search_for()
            position = 'one'
        # TODO: support selection of numbers greater than 5
        pos_as_int = {'one': 0, 'two': 1, 'three': 2, 'four': 3, 'five': 4}
        try:
            position = pos_as_int[position]
        except KeyError:
            # vocalize('Sorry, I have a lazy developer and can only play from the first five results.')
            return

        # click and play
        title_card = self.driver.find_element_by_xpath('//div[@id="title-card-0-{}"]'.format(position))
        ActionChains(self.driver).move_to_element(title_card).perform()
        play_link = self.driver.find_element_by_xpath('//div[@id="title-card-0-{}"]/div/a'.format(position))
        play_link = play_link.get_attribute('href')
        self.driver.get(play_link)
        # go full screen
        self.driver.maximize_window()

        thread_names = [t.name for t in threading.enumerate()]
        # spawn thread to monitor who is watching
        if 'monitor_viewers' not in thread_names:
            Thread(target=self.monitor_viewers, name='monitor_viewers').start()

    def pause_unpause(self, flag='pause'):
        if flag == 'pause' and not self.isPaused:
            # click on netflix page in blank location to ensure the signal works
            pyautogui.click(x=500, y=500)
            # now send spacebar signal to pause
            ActionChains(self.driver).key_down(Keys.SPACE).key_up(Keys.SPACE).perform()
            self.isPaused = True
        elif flag == 'unpause' and self.isPaused:
            # click on netflix page in blank location to ensure the signal works
            pyautogui.click(x=500, y=500)
            # now send spacebar signal to pause
            ActionChains(self.driver).key_down(Keys.SPACE).key_up(Keys.SPACE).perform()
            self.isPaused = False
        else:
            return

    def go_back(self):
        self.driver.get(self.last_url)

    def release_context(self):
        self.isBlocking = False

    def monitor_viewers(self):
        possible_faces = {}
        confirmed_viewers = set()
        possible_exits = {}
        while True:
            frame_data_path = [DATA_DIR, 'public_pickles', 'frame_data.p']
            try:
                frame_data = pickle.load(open(os.path.join('', *frame_data_path), 'rb'))
            except pickle.UnpicklingError:
                print('error loading pickle')
                continue
            except EOFError:
                print('error loading pickle')
                continue

            for name in frame_data['face_names']:
                try:
                    possible_faces[name] += 1
                except KeyError:
                    possible_faces[name] = 1

                if possible_faces[name] > 10:
                    # make sure the face has been confirmed for 10 frames before assigning viewer
                    confirmed_viewers.add(name)

            # once confirmed viewers have been discovered keep track of them
            for viewer in confirmed_viewers:
                if viewer not in frame_data['face_names']:
                    try:
                        possible_exits[viewer] += 1
                    except KeyError:
                        possible_exits[viewer] = 1
                    # if any viewer is gone for more than 10 frames the show pauses
                    if possible_exits[viewer] > 10:
                        self.pause_unpause(flag='pause')
                        possible_exits[viewer] = 0
                        # wait for viewer to get back then unpause immediately
                        while self.isPaused:
                            frame_data = pickle.load(open(os.path.join('', *frame_data_path), 'rb'))
                            if viewer in frame_data['face_names']:
                                self.pause_unpause(flag='unpause')
