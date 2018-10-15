import importlib
import multiprocessing

from Configuration import base
from utils import string
from utils import communication


class App(object):
    """
    Controls Plugin-Plugin and Service-Plugin interactions
    """

    def __init__(self):
        # initialize attributes
        self.plugins = {}
        self.betas = {}
        self.services = {}

        # build a new configuration
        config = base.Configuration()
        config.make()
        self.configuration = config

        # load instances of all the required plugins
        for name in self.configuration.plugins:
            plugin = self._import_package(name)
            self.plugins[name] = plugin  # store plugin types locally

        # load instances of all required betas
        for name in self.configuration.betas:
            beta = self._import_package(name)
            self.betas[name] = beta  # store plugin types locally

        # load instances of all the required services
        for name in self.configuration.services:
            service = self._import_package(name)
            self.services[name] = service  # store service types locally

    def start(self):
        """
        Instantiate all of the Plugins and Services in individual processes
        """
        package_names = [p for p in self.plugins]
        package_names += [b for b in self.betas]
        package_names += [s for s in self.services]

        # use a shared dict to transfer Link obects between processes
        manager = multiprocessing.Manager()
        shared_dict = manager.dict()  # initialize the shared list

        # start all the services
        for name, obj in self.services.items():
            service = obj()
            service.configuration = self.configuration
            process = multiprocessing.Process(target=service.start, args=(shared_dict,))
            process.start()

        # start all the plugins
        for name, obj in self.plugins.items():
            plugin = obj()
            plugin.configuration = self.configuration
            process = multiprocessing.Process(target=plugin.start, args=(shared_dict,))
            process.start()

        # start all the betas
        for name, obj in self.betas.items():
            beta = obj()
            beta.configuration = self.configuration
            process = multiprocessing.Process(target=beta.start, args=(shared_dict,))
            process.start()

        # activate sleep plugin to get started
        request = communication.PluginLink(producer='app', consumer='SleepPlugin', command_string='sleep')
        shared_dict[id(request)] = request

        while True:
            continue  # keep the main process alive to prevent manager exit

    @staticmethod
    def _import_package(name):
        """
        Load a Plugin or Service object into memory
        :param name: name of the package to import
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
            alpha_name, beta_name = name.split('.')
            a = "Plugins"
            b = alpha_name
            c = string.pascal_case_to_snake_case(beta_name)
            name = beta_name
        else:
            raise ValueError("unknown package type: {}".format(name))

        import_str = "{}.{}.{}".format(a, b, c)
        module = importlib.import_module(import_str)
        pkg = getattr(module, name)
        return pkg  # return non initiated package object
