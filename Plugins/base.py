import pickle
import os
import multiprocessing
import importlib
from selenium import webdriver
from utils import path_utils
from utils import string_utils


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
        self.command = None  # Command object

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

    def initialize(self):
        """
        Starts Plugin operation
        - should only ever be called through one of the pass methods
        """
        self._is_active = True
        self._mainloop()

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

    def load_protocol(self):
        """
        Loads the pickled dict of of plugins and their queues
        :return: (dict)
        """
        pickle_path = os.path.join(self.local_paths.tmp, 'transfer_protocol.p')
        with open(pickle_path, 'rb') as stream:
            protocol = pickle.load(stream)
        return protocol

    def save_protocol(self, protocol):
        """
        Pickles a new protocol (dict of plugin names and their queues)
        """
        pickle_path = os.path.join(self.local_paths.tmp, 'transfer_protocol.p')
        with open(pickle_path, 'wb') as stream:
            pickle.dump(protocol, stream)

    def pass_and_remain(self, name, cmd=None):
        """
        Sends message to make another Plugin active while remaining functional in background
        :param name: (str) name of the Plugin to initialize
        :param cmd: (Command) command to send to plugin
        """
        self._is_active = False
        protocol = self.load_protocol()
        if name in protocol:
            protocol[name].put(cmd)
        else:
            self._initialize_new(name, cmd)

    def pass_and_terminate(self, name, cmd=None):
        """
        Sends message to make another Plugin active then ceases functionality
        :param name: (str) name of the Plugin to initialize
        :param cmd: (Command) command to send to plugin
        """
        new_protocol = self.load_protocol()
        new_protocol.pop(self.name)  # remove self from protocol
        self.save_protocol(new_protocol)  # save modified protocol
        self.pass_and_remain(name, cmd)
        os.kill(os.getpid(), 9)

    def _initialize_new(self, name, cmd=None):
        """
        Initializes a new Plugin while remaining functional in background
        :param name: (str) name of plugin to initialize
        :param cmd: (Command) command to initialize with
        """
        import_str = "{}.{}.{}".format("Plugins",
                                       name,
                                       string_utils.pascal_case_to_snake_case(name))
        module = importlib.import_module(import_str)
        plugin = getattr(module, name)
        plugin = plugin()
        new_protocol = self.load_protocol()
        new_protocol[plugin.name] = multiprocessing.Queue()
        new_protocol[plugin.name].put(cmd)
        multiprocessing.Process(target=plugin.initialize, name=plugin.name).start()
        self.save_protocol(new_protocol)

    # TODO: make this private like self._initialize_new()
    def initialize_beta(self, name, data, cmd=None):
        """
        Initializes one of the Plugin's BetaPlugins while remaining functional in background
        :param name: (str) name of the beta plugin to initialize
        :param data: any object to pass to the beta
        :param cmd: (Command) command to initialize the beta with
        """
        self._is_active = False
        import_str = "{}.{}.{}".format("Plugins",
                                       self.name,
                                       string_utils.pascal_case_to_snake_case(name))
        module = importlib.import_module(import_str)
        beta = getattr(module, string_utils.snake_case_to_pascal_case(name))
        beta = beta()
        _name = "{}.{}".format(self.name, name)
        multiprocessing.Process(target=beta.initialize, args=(cmd, data), name=_name).start()

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

    def _mainloop(self):
        """
        Keeps the Plugin active
        """
        protocol = self.load_protocol()
        queue = protocol[self.name]
        while True:
            if self._is_active:
                if queue.empty:  # listen for microphone input
                    cmd = self.get_command()
                else:  # get command from the queue
                    cmd = queue.get()
                self._function_handler(cmd)

    def _function_handler(self, cmd):
        """
        Processes a Command object
        :param cmd: (Command) command to process
        """
        if self.accepts_command(cmd):
            self.command = cmd  # store as attribute to acces the object from other methods
            cmd.command_hook()


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
        self.COMMAND_HOOK_DICT[self.exit_context] = ['exit context']
        self.MODIFIERS['exit_context'] = {}

    def initialize(self, cmd=None):
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
