import pickle
import os
import socket
from queue import Queue
import importlib
from multiprocessing import Process
from threading import Thread
import struct
from selenium import webdriver
from utils import path_utils


class Plugin(object):
    """
    Refer to /Plugins/README.md for in depth documentation on this object
    """

    def __init__(self, command_hook_dict, modifiers, name):
        # process args
        self.COMMAND_HOOK_DICT = command_hook_dict
        self.MODIFIERS = modifiers
        self.name = name

        # initialize attributes
        self.local_paths = path_utils.LocalPaths()  # convenience object to return paths
        self._is_active = False  # inform the plugin of its active status
        self.send_queue = Queue()  # queue to send message
        self.listen_queue = Queue()  # queue to get message
        self.cs = None  # client server object goes here

    @property
    def configuration(self):
        """
        Loads the configuration.p file
        :return: Configuration object
        """
        pickle_path = os.path.join(self.local_paths.tmp, 'configuration.p')
        with open(pickle_path, 'rb') as stream:
            config = pickle.load(stream)
        return config

    @property
    def webdriver(self, options=None):
        """
        Generates a selenium.webdriver object
        :return: selenium.webdriver object
        """
        # CHROME_PROFILE_PATH = self.config_obj.environment_variables['Base']['CHROME_PROFILE_PATH']
        CHROMEDRIVER_PATH = os.path.join(self.local_paths.bin, 'chromedriver')

        # set default options
        if options is None:
            '''
            options = webdriver.ChromeOptions()
            options.add_argument("--user-data-dir={}".format(CHROME_PROFILE_PATH))
            options.add_argument("--disable-infobars")
            options.add_argument("--window-size=1920,1080")
            options.add_experimental_option('excludeSwitches', ['disable-component-update'])
            '''
            # options = webdriver.chrome.options.Options()
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-default-apps')
            options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                  options=options)
        return driver

    @property
    def web_app_url(self):
        """
        Wraps FlaskService to determine appropriate URL for localhost webapp
        :return: (str) url
        """
        port = self.configuration.environment_variables['FlaskService']['PORT']
        host = self.configuration.environment_variables['FlaskService']['HOST']
        return "{}:{}/{}".format(host, port, self.name)

    ##################
    # PUBLIC METHODS #
    ##################

    def accepts_command(self, command):
        """
        Checks whether or not the plugin accepts a Command object
        :param: (str) or (Command)
                - if (str): creates command object from string and parses to check
                - if (Command): checks directly
        :return: (bool)
        """
        if type(command) == str:
            command = Command(input_string=command,
                              command_hook_dict=self.COMMAND_HOOK_DICT,
                              modifiers=self.MODIFIERS)
            if command.command_hook:
                accept = True
            else:
                accept = False
        elif type(command) == Command:
            if command.command_hook:
                accept = True
            else:
                accept = False
        else:
            raise TypeError("command must be type str or Command")

        return accept

    def pass_and_remain(self):
        """
        Sends message to make another Plugin active while remaining functional in background
        """

    def pass_and_terminate(self):
        """
        Sends message to make another Plugin active then ceases functionality
        """

    def initialize_and_remain(self):
        """
        Initializes a new Plugin while remaining functional in background
        """

    def initialize_and_terminate(self):
        """
        Initializes a new Plugin then ceases functionality
        """

    def initialize_beta(self):
        """
        Initializes one of the Plugin's BetaPlugins while remaining functional in background
        """

    ####################
    # SERVICE WRAPPERS #
    ####################

    def get_command(self, pre_buffer=None, post_buffer=1, maximum=10):
        """
        Wraps ListenerService to collect vocal command from user via microphone
        :param pre_buffer: seconds to wait for command without hearing anything
                           - None indicates infinite wait time
        :param post_buffer: seconds to wait after volume dips below threshold
        :param maximum: maximum seconds to wait
        :return: Command object
        """
        # call the listener service and collect response
        signal_fname = self.configuration.services['ListenerService']['input_filename']
        response_fname = self.configuration.services['ListenerService']['output_filename']

        # create the params file for the service to read
        params_dict = {'pre_buffer': pre_buffer,
                       'post_buffer': post_buffer,
                       'maximum': maximum,
                       'reset_threshold': False}
        with open(signal_fname, 'wb') as stream:
            pickle.dump(params_dict, stream)

        # wait for the response
        while not os.path.isfile(response_fname):
            continue

        # once the file exists read its content
        with open(response_fname, 'r') as f:
            command = f.read()
        os.remove(response_fname)  # delete the response file

        # convert to Command object
        command = Command(input_string=command,
                          command_hook_dict=self.COMMAND_HOOK_DICT,
                          modifiers=self.MODIFIERS)

        return command

    def reset_threshold(self):
        """
        Wraps ListenerService to reset the noise/signal threshold
        """
        path = self.configuration.services['ListenerService']['input_filename']
        _d = {'reset_threshold': True}
        while os.path.isfile(path):  # wait for last process to complete
            continue

        with open(path, 'wb') as stream:
            pickle.dump(_d, stream)

        while os.path.isfile(path):  # wait for processing to complete
            continue

    def vocalize(self, text):
        """
        Wraps SpeakerService to use TTS engine
        :param text: (str) words to be spoken by TTS
        """
        assert type(text) == str
        path = self.configuration.services['SpeakerService']['input_filename']
        while os.path.isfile(path):  # wait for last process to complete
            continue

        with open(path, 'w') as stream:
            stream.write(text)

        while os.path.isfile(path):  # wait for processing to complete
            continue

    ###################
    # PRIVATE METHODS #
    ###################

    def _initialize(self):
        """
        Starts Plugin operation
        """

    def _make_active(self):
        """
        Sets self.is_active to True
        """

    def _mainloop(self):
        """
        Keeps the Plugin active
        """

    def _function_handler(self):
        """
        Processes a Command object
        """


class BetaPlugin(Plugin):
    """
    Refer to /Plugins/README.md for in depth documentation on this object
    """

    def __init__(self, command_hook_dict, modifiers, name, alpha_name):
        # process args
        self.COMMAND_HOOK_DICT = command_hook_dict
        self.MODIFIERS = modifiers
        self.name = name

        self.alpha_name = alpha_name  # store the alpha plugin's name
        self.DATA = None  # the data passed by the alpha plugin

        super().__init__(command_hook_dict=command_hook_dict,
                         modifiers=modifiers,
                         name=self.name)  # initialize alpha Plugin

        # add exit context as a command for all betas
        self.COMMAND_HOOK_DICT['exit_context'] = ['exit context']
        self.MODIFIERS['exit_context'] = {}

    def initialize(self):
        """
        Initialize the BetaPlugin
        """

    def exit_context(self):
        """
        Returns control to the alpha Plugin
        """


class Command(object):
    """
    Used to process vocal commands in a modular and easily parse-able way
    """

    def __init__(self, input_string, command_hook_dict, modifiers):
        # process args
        self.input_string = input_string
        self.command_hook_dict = command_hook_dict
        self.modifiers = modifiers

        # initialize attributes
        self._command_hook = ''
        self._premodifier = ''
        self._modifier = ''
        self._postmodifier = ''

    @property
    def command_hook(self):
        """
        Returns the command hook found in self.input string
        :return: (str)
        """
        return self._command_hook

    @property
    def premodifier(self):
        """
        Returns the premodifier found in self.input string
        :return: (str)
        """
        return self._premodifier

    @property
    def modifier(self):
        """
        Returns the modifier found in self.input_string
        :return: (str)
        """
        return self._modifier

    @property
    def postmodifier(self):
        """
        Returns the postmodifier found in self.input_string
        :return: (str)
        """
        return self._postmodifier

    def parse(self):
        """
        Sets all of the properties by scanning self.input_string
        """
        _input = self.input_string

        # find command hook
        for hook, spellings in self.command_hook_dict.items():
            for spelling in spellings:
                if spelling in _input:
                    self._command_hook = hook
                    _input = _input.replace(spelling, '', 1)  # remove first instance of the hook

        if not self.command_hook:  # inputs with no command hook are not processed
            return

        # find modifier
        target_modifier = self.modifiers[self.command_hook]
        for modifier, spellings in target_modifier.items():
            for spelling in spellings:
                if spelling in _input:
                    self._modifier = modifier

        # find premodifier and postmodifier
        if self.modifier:
            _input = _input.split(self.modifier)
            self._premodifier = _input[0]
            if len(_input) > 1:
                self._postmodifier = ''.join(_input[1:])
        else:
            self._premodifier = _input  # if no modifier is detected everythin else is premodifier


class ClientServer(object):
    """
    Object used to synchronize broadcast-style messaging between Plugins
    - This class is incredibly sensitive and honestly I'm not entirely sure why it works
    - Future updates will be required to improve robustness
    """

    def __init__(self,
                 port,
                 port_list,
                 send_queue,
                 listen_queue,
                 group='224.3.29.71'):
        self.port = port
        self.port_list = port_list
        self.send_queue = send_queue
        self.listen_queue = listen_queue
        self.group = group

    def send(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create the datagram socket
        sock.settimeout(0.25)  # prevents indefinite blocking
        ttl = struct.pack('b', 1)  # set time-to-live as 1
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        while True:
            # get message to send from the queue
            if not self.send_queue.empty():
                message = self.send_queue.get()
                if message == 'quit':
                    break
            else:
                continue
            for p in self.port_list:
                sock.sendto(message.encode(), (self.group, p))
                '''
                ------------------------------------------------------------------
                If I wanted to do a response based check this is how it would work

                # Look for responses from all recipients
                while True:
                    try:
                        data, server = sock.recvfrom(16)
                    except socket.timeout:
                        break
                    else:
                        print(' {} received {} from {}'.format(self.port,
                                                               data,
                                                               server))
                ------------------------------------------------------------------
                '''

    def listen(self):
        server_address = ('', self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create the socket
        sock.bind(server_address)  # Bind to the server address

        # Tell the OS to add the socket to the multicast group on all interfaces.
        group = socket.inet_aton(self.group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # Receive/respond loop
        while True:
            data, address = sock.recvfrom(1024)
            self.listen_queue.put(data)

            '''
            ---------------------------------------------------------------------
            If I wanted to use acknowledgement messages this is how I would do it

            print(' {} sending acknowledgement to {}'.format(self.port,
                                                             address))
            sock.sendto('ack'.encode(), address)
            ---------------------------------------------------------------------
            '''