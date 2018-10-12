import importlib
import multiprocessing

from Configuration import base
from utils import string
from utils import parallelization
from utils import communication


class App(object):
    """
    Controls Plugin-Plugin and Service-Plugin interactions
    """

    def __init__(self):
        # initialize attributes
        self.plugins = {}
        self.services = {}
        self.queues = {}

        # build a new configuration
        config = base.Configuration()
        config.make()
        self.configuration = config

        # load instances of all the required plugins
        for name in self.configuration.plugins:
            plugin = self._import_package(name)
            self.plugins[name] = plugin  # store plugin types locally

        # load instances of all the required services
        for name in self.configuration.services:
            service = self._import_package(name)
            self.services[name] = service  # store service types locally
        # TODO: process betas somehow

    def start(self):
        """
        Instantiate all of the Plugins and Services in individual processes
        """
        manager = multiprocessing.Manager()

        # start all the services
        for name, obj in self.services.items():
            queue = parallelization.TwoWayProcessQueue(manager)
            self.queues[name] = queue
            service = obj()
            service.configuration = self.configuration
            process = multiprocessing.Process(target=service.start, args=(queue,))
            process.start()

        # start all the plugins
        for name, obj in self.plugins.items():
            queue = parallelization.TwoWayProcessQueue(manager)
            self.queues[name] = queue
            plugin = obj()
            plugin.configuration = self.configuration
            process = multiprocessing.Process(target=plugin.start, args=(queue,))
            process.start()

        # activate sleep plugin
        queue = self.queues['SleepPlugin']
        request = communication.PluginRequest(plugin_name='SleepPlugin', command_string='sleep')
        queue.server_put(request)

        self._monitor_queues()  # listen for requests

    def _monitor_queues(self):
        """
        Handles incoming data from Plugins and Services
        """
        package_names = [p for p in self.plugins] + [s for s in self.services]
        while True:
            for name in package_names:
                if name in self.queues:
                    queue = self.queues[name]
                    if not queue.client_empty():
                        request = queue.client_get()
                        self._process_request(request)

    def _process_request(self, request):
        """
        Redirects Request objects to the proper target
        :param request: (communication_utils.Request)
        """
        if request.outgoing:
            queue = self.queues[request.send_name]  # send the request from requester to processor
            queue.server_put(request)
        else:
            queue = self.queues[request.return_name]  # send the request back from processor to requester
            queue.server_put(request)

    @staticmethod
    def _import_package(name, alpha_name=None):
        """
        Load a Plugin or Service object into memory
        :param name: name of the package to import
        :param alpha_name: name of the BetaPlugin's Alpha
        :return: (Plugin or Service)
        """
        if name.endswith("Plugin"):
            a = "Plugins"
            b = name
            c = string.pascal_case_to_snake_case(name)
        elif name.endswith("Service"):
            a = "Services"
            b = name
            c = string.pascal_case_to_snake_case(name)
        elif name.endswith("Beta"):
            a = "Plugins"
            b = alpha_name
            c = string.pascal_case_to_snake_case(name)
        else:
            raise ValueError("unknown package type: {}".format(name))

        import_str = "{}.{}.{}".format(a, b, c)
        module = importlib.import_module(import_str)
        pkg = getattr(module, name)
        return pkg  # return non initiated package object
