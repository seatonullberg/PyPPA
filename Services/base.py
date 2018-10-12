import datetime
from utils import path


class Clock(object):

    def __init__(self):
        self._since_init = datetime.datetime.now()
        self._since_active = None
        self._since_output = None

    def update(self, flag):
        if flag == 'active':
            self._since_active = datetime.datetime.now()
        elif flag == 'output':
            self._since_output = datetime.datetime.now()
        else:
            raise ValueError("flag must be 'active' or 'output'")

    @property
    def since_init(self):
        delta = datetime.datetime.now() - self._since_init
        return delta.total_seconds()

    @property
    def since_active(self):
        if self._since_active is None:
            return -1
        else:
            delta = datetime.datetime.now() - self._since_active
            return delta.total_seconds()

    @property
    def since_output(self):
        if self._since_output is None:
            return -1
        else:
            delta = datetime.datetime.now() - self._since_output
            return delta.total_seconds()


class Service(object):

    def __init__(self, name, target):
        self.name = name
        self.target = target

        self.queue = None
        self.configuration = None
        self.input_data = None
        self._request = None
        self.local_paths = path.LocalPaths()  # convenience object to return paths

    def start(self, queue):
        self.queue = queue
        while True:
            if not self.queue.server_empty():
                self._request = self.queue.server_get()
                self.input_data = self._request.data
                self.target()

    def respond(self, output_data):
        self._request.data = output_data
        self._request.respond(self.queue)

    def environment_variable(self, key, base=False):
        """
        Reads an environment variable from the configuration
        :param key: (str) the environment variable key/name
        :param base: (bool) indicates if the environment variable is a base environment variable
        :return: (str) the requested environment variable value
        """
        if base:
            value = self.configuration.environment_variables['BASE'][key]
        else:
            value = self.configuration.environment_variables[self.name][key]
        return value
