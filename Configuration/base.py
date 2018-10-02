import os
import pickle
import importlib
import yaml
import exceptions  # custom exceptions
from utils import string_utils  # custom string utility functions


class Configuration(object):
    """
    Refer to /Configuration/README.md for in depth documentation of this object
    """

    def __init__(self):
        self._port_map = {}
        self._environment_variables = {}
        self._plugins = {}
        self._services = {}
        self._blacklist = []

    @property
    def working_path(self):
        path = os.path.dirname(__file__)
        path = os.path.dirname(path)
        return path  # return the /PyPPA/ directory path

    @property
    def yaml_path(self):
        return os.path.join(self.working_path,
                            'Configuration',
                            'configuration.yaml')  # returns the path to the yaml config

    @property
    def pickle_path(self):
        return os.path.join(self.working_path,
                            'tmp',
                            'configuration.p')  # returns the path to configuration pickle

    @property
    def log_path(self):
        return os.path.join(self.working_path,
                            'Configuration',
                            'configuration.log')  # returns the path to the configuration error log

    @property
    def port_map(self):
        return self._port_map

    @property
    def environment_variables(self):
        return self._environment_variables

    @property
    def plugins(self):
        return self._plugins

    @property
    def services(self):
        return self._services

    @property
    def blacklist(self):
        return self._blacklist

    @property
    def environment_fn(self):
        return 'environment.txt'

    def make(self):
        """
        Builds yaml and pickle configuration files from the information
        provided in the environment.txt and autoconfig.py files
        """
        self._clear_log()

        if os.path.isfile(self.yaml_path):
            self._read_yaml()

        self._scan_base()
        self._scan_plugins()
        self._scan_services()
        self._set_port_map()
        self._write_yaml()
        self._write_pickle()

        if os.path.isfile(self.log_path):
            raise exceptions.ConfigurationError("The configuration is incomplete. "
                                                "Open {} to see details".format(self.log_path))

    def _read_yaml(self):
        """
        Sets self._environment_variables and self._blacklist from the yaml configuration file
        """
        with open(self.yaml_path, 'r') as stream:
            config = yaml.load(stream)
            self._environment_variables = config['ENVIRONMENT_VARIABLES']
            self._blacklist = [key for key, value in config['BLACKLIST'].items() if value]  # list of blacklisted pkgs

    def _write_yaml(self):
        """
        Uses the available configuration information to write a yaml configuration file
        """
        # add environment variables
        to_yaml = {}
        to_yaml['ENVIRONMENT_VARIABLES'] = self.environment_variables
        # add blacklist
        plugin_packages = os.listdir(os.path.join(self.working_path, 'Plugins'))
        service_packages = os.listdir(os.path.join(self.working_path, 'Services'))
        packages = plugin_packages + service_packages
        blacklist_as_dict = {}
        for pkg in packages:
            if pkg in self.blacklist:
                blacklist_as_dict[pkg] = True
            else:
                blacklist_as_dict[pkg] = False
        to_yaml['BLACKLIST'] = blacklist_as_dict
        # dump all to yaml file
        with open(self.yaml_path, 'w') as stream:
            yaml.dump(to_yaml, stream)

    def _write_pickle(self):
        """
        Creates a pickle file of this Configuration object
        """
        with open(self.pickle_path, 'wb') as stream:
            pickle.dump(self, stream)

    def _scan_base(self):
        """
        Sets the environment variables for the Base environment.txt file
        """
        base_path = os.path.join(self.working_path, self.environment_fn)
        if 'Base' not in self._environment_variables:
            self._environment_variables['Base'] = {}

        with open(base_path, 'r') as stream:
            environment_variables = [line.strip() for line in stream]

        for var in environment_variables:
            if var not in self._environment_variables['Base']:
                self._environment_variables['Base'][var] = ''  # set blanks for unfilled environment variables
        # Base environment variables do not get autoconfig

    def _scan_plugins(self):
        """
        Collects the required configuration information from all plugins in /Plugins/
        """
        plugins_path = os.path.join(self.working_path, 'Plugins')
        plugin_pkgs = os.listdir(plugins_path)
        plugin_pkgs = [pkg for pkg in plugin_pkgs if pkg not in self.blacklist]
        plugin_pkgs.remove('base.py')
        plugin_pkgs.remove('README.md')
        plugin_pkgs.remove('__pycache__')
        for pkg in plugin_pkgs:
            self._set_environment_variables(pkg)
            self._set_beta_plugins(pkg)
            self._set_command_hook_dict(pkg)
            self._set_modifiers(pkg)

    def _scan_services(self):
        """
        Collects the required configuration information from all services in /Services/
        """
        services_path = os.path.join(self.working_path, 'Services')
        service_pkgs = os.listdir(services_path)
        service_pkgs = [pkg for pkg in service_pkgs if pkg not in self.blacklist]
        service_pkgs.remove('base.py')
        service_pkgs.remove('README.md.py')
        service_pkgs.remove('__pycache__')
        for pkg in service_pkgs:
            self._set_environment_variables(pkg)
            self._set_io_filenames(pkg)

    def _set_environment_variables(self, package_name):
        """
        Sets the environment variables of a package from yaml or autoconfig
        :param package_name: (str) name of the plugin or service package
        """
        if package_name not in self._environment_variables:
            self._environment_variables[package_name] = {}

        environment_path = os.path.join(self.working_path,
                                        '{}',
                                        package_name,
                                        self.environment_fn)

        if package_name.endswith('Plugin'):
            environment_path = environment_path.format('Plugins')
        elif package_name.endswith('Service'):
            environment_path = environment_path.format('Services')
        else:
            raise ValueError("invalid package_name")

        with open(environment_path, 'r') as stream:
            environment_variables = [line.strip() for line in stream]

        for var in environment_variables:
            if var not in self._environment_variables[package_name]:
                self._environment_variables[package_name][var] = ''  # set blanks for unfilled environment variables

        for var in environment_variables:
            if not self._environment_variables[package_name][var]:
                # attempt to use a provided autoconfig.py file to set the environment variable
                try:
                    self._environment_variables[package_name][var] = self._autoconfig(package_name, var)
                except ImportError:
                    with open(self.log_path, 'a') as stream:
                        stream.write("{p} requires a value for the environment variable: {v}\n".format(
                            p=package_name,
                            v=var
                        ))

    def _set_beta_plugins(self, package_name):
        """
        Sets self._plugins[package_name][betas]
        :param package_name: (str) name of the plugin package
        """
        if package_name not in self._plugins:
            self._plugins[package_name] = {}

        if 'betas' not in self._plugins[package_name]:
            self._plugins[package_name]['betas'] = {}

        plugin_path = os.path.join(self.working_path,
                                   'Plugins',
                                   package_name)

        for filename in os.listdir(plugin_path):
            if filename.endswith('beta.py'):
                beta_name = filename.replace('.py', '')  # remove the .py to get the ClassName of the beta plugin
                beta_name = string_utils.snake_case_to_pascal_case(beta_name)
                self._plugins[package_name]['betas'][beta_name] = {}
                self._set_command_hook_dict(package_name, filename)
                self._set_modifiers(package_name, filename)

    def _set_command_hook_dict(self, package_name, beta_filename=None):
        """
        Sets self._plugins[package_name]['command_hook_dict'] with the respective plugin's COMMAND_HOOK_DICT
        :param package_name: (str) name of the plugin package
        :param beta_filename: (str) name of the beta filename to retrieve from if provided
        """
        # define these to save line space
        SNAKE_PLUGIN = string_utils.pascal_case_to_snake_case(package_name)
        PASCAL_PLUGIN = package_name
        if beta_filename is not None:
            SNAKE_BETA = beta_filename.replace('.py', '')
            PASCAL_BETA = string_utils.snake_case_to_pascal_case(SNAKE_BETA)
        else:
            SNAKE_BETA = None
            PASCAL_BETA = None

        if PASCAL_PLUGIN not in self._plugins:
            self._plugins[PASCAL_PLUGIN] = {}

        if beta_filename is None:
            import_str = "{}.{}.{}".format('Plugins',
                                           PASCAL_PLUGIN,
                                           SNAKE_PLUGIN)
            module = importlib.import_module(import_str)
            plugin = getattr(module,
                             PASCAL_PLUGIN)
            plugin = plugin()
            command_hook_dict = getattr(plugin, 'COMMAND_HOOK_DICT')
            self._plugins[PASCAL_PLUGIN]['command_hook_dict'] = command_hook_dict
        else:
            import_str = "{}.{}.{}".format('Plugins',
                                           PASCAL_PLUGIN,
                                           SNAKE_BETA)
            module = importlib.import_module(import_str)
            beta_plugin = getattr(module,
                                  PASCAL_BETA)
            beta_plugin = beta_plugin()
            command_hook_dict = getattr(beta_plugin, 'COMMAND_HOOK_DICT')
            self._plugins[PASCAL_PLUGIN]['betas'][PASCAL_BETA]['command_hook_dict'] = command_hook_dict

    def _set_modifiers(self, package_name, beta_filename=None):
        """
        Sets self._plugins[package_name]['modifiers'] with the respective plugin's MODIFIERS
        :param package_name: (str) name of the plugin package
        :param beta_filename: (str) name of the beta filename to retrieve from if provided
        """
        # define these to save line space
        SNAKE_PLUGIN = string_utils.pascal_case_to_snake_case(package_name)
        PASCAL_PLUGIN = package_name
        if beta_filename is not None:
            SNAKE_BETA = beta_filename.replace('.py', '')
            PASCAL_BETA = string_utils.snake_case_to_pascal_case(SNAKE_BETA)
        else:
            SNAKE_BETA = None
            PASCAL_BETA = None

        if PASCAL_PLUGIN not in self._plugins:
            self._plugins[PASCAL_PLUGIN] = {}

        if beta_filename is None:
            import_str = "{}.{}.{}".format('Plugins',
                                           PASCAL_PLUGIN,
                                           SNAKE_PLUGIN)
            module = importlib.import_module(import_str)
            plugin = getattr(module,
                             PASCAL_PLUGIN)
            plugin = plugin()
            modifiers = getattr(plugin, 'MODIFIERS')
            self._plugins[PASCAL_PLUGIN]['modifiers'] = modifiers
        else:
            import_str = "{}.{}.{}".format('Plugins',
                                           PASCAL_PLUGIN,
                                           SNAKE_BETA)
            module = importlib.import_module(import_str)
            beta_plugin = getattr(module,
                                  PASCAL_BETA)
            beta_plugin = beta_plugin()
            modifiers = getattr(beta_plugin, 'MODIFIERS')
            self._plugins[PASCAL_PLUGIN]['betas'][PASCAL_BETA]['modifiers'] = modifiers

    def _set_io_filenames(self, package_name):
        """
        Sets self._services[package_name] with the input and output filenames for the service
        :param package_name: (str) name of the service package
        """
        # define these to save line space
        PASCAL_SERVICE = package_name
        SNAKE_SERVICE = string_utils.pascal_case_to_snake_case(PASCAL_SERVICE)

        if PASCAL_SERVICE not in self._services:
            self._services[PASCAL_SERVICE] = {}

        import_str = "{}.{}.{}".format('Services',
                                       PASCAL_SERVICE,
                                       SNAKE_SERVICE)
        module = importlib.import_module(import_str)
        service = getattr(module,
                          PASCAL_SERVICE)
        service = service()
        fn_in = getattr(service, 'input_filename')
        fn_out = getattr(service, 'output_filename')
        self._services[PASCAL_SERVICE]['input_filename'] = fn_in
        self._services[PASCAL_SERVICE]['output_filename'] = fn_out

    def _set_port_map(self):
        """
        Sets self._port_map with an intger value for every plugin/beta key
        """
        PORT = 5555
        for key in self.plugins:
            self._port_map[key] = PORT
            PORT += 1
            for beta in self.plugins[key]['betas']:
                self._port_map[beta] = PORT
                PORT += 1

    def _autoconfig(self, package_name, key):
        """
        Sets self._environment_variables[plugin_package][key] with a value from plugin_package's autoconfig.py file
        :param package_name: (str) name of the plugin package
        :param key: (str) name of he environment variable to set
        """
        import_str = "{}.{}.autoconfig"
        if package_name.endswith('Plugin'):
            import_str = import_str.format('Plugins',
                                           package_name)
        elif package_name.endswith('Service'):
            import_str = import_str.format('Services',
                                           package_name)
        else:
            raise ValueError("invalid package_name")

        # if an import error is raised because of a missing autoconfig.py file or a missing
        # corresponding function it will be handled in self._set_environment_variables
        module = importlib.import_module(import_str)
        autoconfig_function = getattr(module, key)  # use function which corresponds to key for autoconfig
        value = autoconfig_function()  # return value is the value of the environment variable
        self._environment_variables[package_name][key] = value

    def _clear_log(self):
        """
        Deletes the error log file
        """
        if os.path.isfile(self.log_path):
            os.remove(self.log_path)


if __name__ == "__main__":
    o = Configuration()
    o.make()
