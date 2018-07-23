from base_beta import BaseBeta
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pyautogui
from threading import Thread
from queue import Queue
import pickle


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
        self.monitor_queue = Queue()
        self.monitor_thread = None

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
        self.status = 'play'
        # spawn a thread to monitor the viewers
        if self.monitor_thread is None:
            self.monitor_thread = Thread(target=self._monitor_viewers, args=(self.monitor_queue,))
            self.monitor_thread.start()

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
        self.monitor_queue.put('quit')
        self.DATA.quit()
        super().exit_context(cmd)

    def _monitor_viewers(self, q):
        initial_viewer = None
        candidates = {}
        exit_count = 0
        quit_signal = False
        while not quit_signal:
            # load the frame data from pickle file
            try:
                face_names = self.frame_data['face_names']
            except pickle.UnpicklingError:
                face_names = []
            except EOFError:
                face_names = []

            if not q.empty():
                if q.get() == 'quit':
                    quit_signal = True
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
            else:
                if initial_viewer not in face_names:
                    exit_count += 1
                # after a 25 frame exit reset the counters and pause netflix
                if exit_count > 25:
                    candidates = {}
                    exit_count = 0
                    initial_viewer = None
                    self.pause()

