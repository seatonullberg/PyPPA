import os
import pickle
from selenium import webdriver

from utils import path
from utils import communication


class Plugin(object):
    """
    Refer to /Plugins/README.md for in depth documentation on this object
    """

    def __init__(self, command_hooks, modifiers, name):
        # process args
        self.command_hooks = command_hooks
        self.modifiers = modifiers
        self.name = name
        self.shared_dict = None  # defined by App to allow data transfer between processes

        # initialize attributes
        self.command = None  # used by subclasses to process the current command
        self.configuration = None  # this gets defined by App
        self.is_active = False  # indicates if the mainloop has started in a new process
        self.local_paths = path.LocalPaths()  # convenience object to return paths

    @property
    def webdriver(self, options=None):
        """
        Generates a selenium.webdriver object
        :return: selenium.webdriver object
        """
        # CHROME_PROFILE_PATH = self.config_obj.environment_variables['Base']['CHROME_PROFILE_PATH']
        # chromedriver_path = os.path.join(self.local_paths.bin, 'chromedriver')
        chromedriver_path = self.request_environment_variable('CHROMEDRIVER_PATH', base=True)
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

        driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
        return driver

    def start(self, shared_dict):
        """
        Keep the plugin process active
        - should only be called by the app context
        """
        self.shared_dict = shared_dict
        while True:
            self.command = None
            for key, link in self.shared_dict.items():
                if link.consumer == self.name and not link.complete:
                    link = self.shared_dict.pop(key)
                    self._process_link(link)
            if self.is_active:
                if self.command is None:
                    self.command = self.get_command()
                if self._accepts_command(self.command):
                    self.command.command_hook()
                print(self.is_active)

    # TODO:
    def process_data_link(self, link):
        """
        This method describes the package's response to an arbitrary DataRequest
        :param request: (communication.DataRequest)
        """
        return link

    ############
    # WRAPPERS #
    ############

    def request_plugin(self, plugin_name, command_string):
        """
        Sends PluginRequest and sets self.is_active = False
        :param plugin_name: (str) name of the Plugin to initialize
                            - if None: call first plugin to accept the command
        :param command_string: (str) command to send to plugin
        """
        self.is_active = False
        if plugin_name is None:
            for pname in self.configuration.plugins:
                response = self.request_acceptance(plugin_name=pname, command_string=command_string)
                if response.fields['result']:
                    plugin_name = pname
                    break

        if plugin_name is None:
            raise ValueError("none of the installed plugins accept the command: {}".format(command_string))

        request = communication.PluginLink(producer=self.name,
                                           consumer=plugin_name,
                                           command_string=command_string)
        request.key = id(request)
        self.shared_dict[request.key] = request
        self._wait_response(request.key)  # no need to get return value in this case

    def request_data(self, package_name, input_data):
        """
        Sends DataRequest and awaits response
        :param package_name: (str) name of Service or Plugin to send data to
        :param input_data: object to send to the service from processing
        :return: response from service
        """
        request = communication.DataLink(producer=self.name,
                                         consumer=package_name,
                                         input_data=input_data)
        request.key = id(request)
        self.shared_dict[request.key] = request
        return self._wait_response(request.key)

    def request_acceptance(self, plugin_name, command_string):
        """
        Requests if plugin_name accepts the proposed command
        :param plugin_name: (str) Plugin to send to
        :param command_string: (str) command to test
        :return: (bool) indicating is command is accepted
        """
        request = communication.AcceptanceLink(producer=self.name,
                                               consumer=plugin_name,
                                               command_string=command_string)
        request.key = id(request)
        self.shared_dict[request.key] = request
        return self._wait_response(request.key)

    def request_cache(self, package_name):
        # not a real request type
        cache_file = os.path.join(self.local_paths.tmp, "{}.cache".format(package_name))
        with open(cache_file, 'rb') as stream:
            result = pickle.load(stream)
        return result

    def request_environment_variable(self, key, base=False):
        # not a real request type
        if base:
            value = self.configuration.environment_variables['Base'][key]
        else:
            value = self.configuration.environment_variables[self.name][key]
        return value

    def get_command(self, pre_buffer=None, post_buffer=1, maximum=10):
        """
        Wraps ListenerService to collect vocal command from user via microphone
        :param pre_buffer: seconds to wait for command without hearing anything
                           - None indicates infinite wait time
        :param post_buffer: seconds to wait after volume dips below threshold
        :param maximum: maximum seconds to wait
        :return: Command object
        """
        # create the params to send
        params_dict = {'pre_buffer': pre_buffer,
                       'post_buffer': post_buffer,
                       'maximum': maximum,
                       'reset_threshold': False}
        response = self.request_data("ListenerService", params_dict)
        # convert to Command object
        command = Command(input_string=response.fields['output_data'],
                          command_hooks=self.command_hooks,
                          modifiers=self.modifiers)
        command.parse()
        self.command = command
        return command

    def reset_threshold(self):
        """
        Wraps ListenerService to reset the noise/signal threshold
        """
        threshold_dict = {'reset_threshold': True}
        response = self.request_data("ListenerService", threshold_dict)
        threshold = response.fields['output_data']
        print("old threshold: {}\nnew threshold: {}".format(threshold['old'], threshold['new']))

    def vocalize(self, text):
        """
        Wraps SpeakerService to use TTS engine
        :param text: (str) words to be spoken by TTS
        """
        self.request_data("SpeakerService", text)  # SpeakerService returns None

    def sleep(self):
        """
        Wraps SleepPlugin for simple transfers to inactive state
        """
        self.request_plugin(plugin_name='SleepPlugin',
                            command_string='sleep')

    ###################
    # PRIVATE METHODS #
    ###################

    def _wait_response(self, key):
        while True:
            for _key, link in self.shared_dict.items():
                if _key == key and link.complete:
                    result = self.shared_dict.pop(key)
                    return result

    def _process_link(self, link):
        # plugin
        if isinstance(link, communication.PluginLink):
            link = self._process_plugin_link(link)
        # data
        elif isinstance(link, communication.DataLink):
            link = self._process_data_link(link)
        # acceptance
        elif isinstance(link, communication.AcceptanceLink):
            link = self._process_acceptance_link(link)
        # error
        else:
            raise TypeError("unsupported link type: {}".format(type(link)))

        link.complete = True
        self.shared_dict[link.key] = link

    def _process_plugin_link(self, link):
        self.is_active = True
        command = Command(input_string=link.fields['command_string'],
                          command_hooks=self.command_hooks,
                          modifiers=self.modifiers)
        command.parse()
        self.command = command
        return link

    def _process_data_link(self, link):
        # developers will have to define their own interactions with the data request
        self.process_data_link(link)
        return link

    def _process_acceptance_link(self, link):
        link.fields['result'] = self._accepts_command(link.fields['command_string'])
        return link

    def _accepts_command(self, command):
        """
        Checks whether or not the plugin accepts a Command object
        :param: (str) or (Command)
                - if (str): creates command object from string and parses to check
                - if (Command): checks directly
        :return: (bool)
        """
        if type(command) == str:
            command = Command(input_string=command,
                              command_hooks=self.command_hooks,
                              modifiers=self.modifiers)
            command.parse()

        elif type(command) == Command:
            command.parse()
        else:
            raise TypeError("command must be type str or Command")

        if command.command_hook:
            accept = True
        else:
            accept = False

        return accept


class BetaPlugin(Plugin):
    """
    Refer to /Plugins/README.md for in depth documentation on this object
    """

    def __init__(self, command_hooks, modifiers, name):
        # process args
        self.command_hooks = command_hooks
        self.modifiers = modifiers
        # add exit context as a command for all betas
        self.command_hooks[self.exit_context] = ['exit context']
        self.modifiers[self.exit_context] = {}
        self.name = name

        super().__init__(command_hooks=command_hooks,
                         modifiers=modifiers,
                         name=self.name)  # initialize alpha Plugin

    def exit_context(self):
        """
        Returns control to the alpha Plugin
        """
        alpha_name = self.name.split('.')[0]
        self.request_plugin(alpha_name)


class Command(object):
    """
    Used to process vocal commands in a modular and easily parse-able way
    """

    def __init__(self, input_string, command_hooks, modifiers):
        # process args
        self.input_string = input_string
        self.command_hooks = command_hooks
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
        :return: function to call
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
        for hook, spellings in self.command_hooks.items():
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
                    self._modifier = spelling.strip()

        # find premodifier and postmodifier
        if self.modifier:
            _input = _input.split(self.modifier)
            self._premodifier = _input[0].strip()
            if len(_input) > 1:
                self._postmodifier = ''.join(_input[1:]).strip()
        else:
            self._premodifier = _input.strip()  # if no modifier is detected everythin else is premodifier
