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
        self.queue = None  # this gets defined by the app context

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
        chromedriver_path = self.environment_variable('CHROMEDRIVER_PATH', base=True)
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

    def start(self, queue):
        """
        Keep the plugin process active
        - should only be called by the app context
        """
        self.queue = queue

        while True:
            command = ''
            # check queue for new requests
            if self.queue.server_empty() and self.is_active:
                command = self.get_command()
            else:
                request = self.queue.server_get()
                if type(request) == communication.PluginRequest:  # process plugin request
                    self.is_active = True
                    command_string = request.command_string  # get command from the request
                    command = Command(input_string=command_string,
                                      command_hooks=self.command_hooks,
                                      modifiers=self.modifiers)
                    command.parse()
                elif type(request) == communication.CommandAcceptanceRequest:  # process command accept request
                    cmd = request.command_string
                    result = self._accepts_command(cmd)
                    request.accepts = result  # set the request's attribute prior to responding
                else:
                    raise NotImplementedError()

                request.respond(self.queue)

            # execute any detected command
            if self._accepts_command(command):
                self.command = command
                command.command_hook()

    ############
    # WRAPPERS #
    ############

    def request_plugin(self, plugin_name=None, command_string=None):
        """
        Sends PluginRequest and sets self.is_active = False
        :param plugin_name: (str) name of the Plugin to initialize
                            - if None: call first plugin to accept the command
        :param command_string: (str) command to send to plugin
        """
        self.is_active = False
        if plugin_name is None:
            for pname in self.configuration.plugins:
                accepts = self.request_command_acceptance(plugin_name=pname,
                                                          command_string=command_string)
                if accepts:
                    plugin_name = pname
                    break

        if plugin_name is None:
            raise ValueError("none of the installed plugins accept the command: {}".format(command_string))

        request = communication.PluginRequest(plugin_name=plugin_name,
                                              command_string=command_string)
        request.send(self.queue)

    def request_data(self, package_name, data):
        """
        Sends DataRequest and awaits response
        :param package_name: (str) name of Service or Plugin to send data to
        :param data: object to send to the service from processing
        :return: response from service
        """
        request = communication.DataRequest(send_name=package_name,
                                            return_name=self.name,
                                            data=data)
        request.send(self.queue)
        while self.queue.server_empty():  # all services must out some response in queue to proceed
            continue
        result = self.queue.server_get()
        return result.data

    def request_command_acceptance(self, plugin_name, command_string):
        """
        Requests if plugin_name accepts the proposed command
        :param plugin_name: (str) Plugin to send to
        :param command_string: (str) command to test
        :return: (bool) indicating is command is accepted
        """
        request = communication.CommandAcceptanceRequest(plugin_name=plugin_name,
                                                         return_name=self.name,
                                                         command_string=command_string)
        request.send(self.queue)
        while self.queue.server_empty():
            continue
        result = self.queue.server_get()
        return result.accepts

    def environment_variable(self, key, base=False):
        """
        Reads an environment variable from the configuration
        :param key: (str) the environment variable key/name
        :param base: (bool) indicates if the environment variable is a base environment variable
        :return: (str) the requested environment variable value
        """
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
        command = Command(input_string=response,
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
        print("old threshold: {}\nnew threshold: {}".format(response['old'], response['new']))

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
