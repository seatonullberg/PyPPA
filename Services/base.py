import os
import datetime
import pickle
from utils import path
from utils import communication


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

        self.shared_dict = None
        self.configuration = None
        self.local_paths = path.LocalPaths()  # convenience object to return paths

    def start(self, shared_dict):
        self.shared_dict = shared_dict
        while True:
            for key, link in self.shared_dict.items():
                if link.consumer == self.name and not link.complete:
                    link = self.shared_dict.pop(key)
                    self._process_link(link)

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
        self.shared_dict[id(request)] = request
        return self._wait_response(_id=id(request))

    def request_environment_variable(self, key, base=False):
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

    def request_cache(self, package_name):
        # not a real request type
        cache_file = os.path.join(self.local_paths.tmp, "{}.cache".format(package_name))
        with open(cache_file, 'rb') as stream:
            result = pickle.load(stream)
        return result

    def _wait_response(self, key):
        while True:
            for _key, link in self.shared_dict[self.name].items():
                if _key == key and link.complete:
                    result = self.shared_dict.pop(key)
                    return result

    def process_data_link(self, link):
        # must be implemented by developer
        return link

    def _process_link(self, link):
        # plugin
        if isinstance(link, communication.PluginLink):
            raise NotImplementedError()
        # data
        elif isinstance(link, communication.DataLink):
            link = self._process_data_link(link)
        # acceptance
        elif isinstance(link, communication.AcceptanceLink):
            raise NotImplementedError()
        # error
        else:
            raise TypeError("unsupported link type: {}".format(type(link)))

        link.complete = True
        self.shared_dict[link.key] = link

    def _process_data_link(self, link):
        # developer must implement their own data request handler as in plugins
        link = self.process_data_link(link)
        return link
