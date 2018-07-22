import os
import pickle
import importlib
import stringcase
import yaml
from collections import OrderedDict


class Configuration(object):

    def __init__(self):
        self._port_map = OrderedDict()
        self._environment_variables = OrderedDict()
        self._plugins = OrderedDict()
        self._background_tasks = []

    @property
    def configuration_fn(self):
        return 'configuration.yaml'

    @property
    def environment_fn(self):
        return 'environment.txt'

    @property
    def configuration_pickle_fn(self):
        return 'configuration.p'

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
    def background_tasks(self):
        return self._background_tasks

    def make(self):
        # read the user configuration to check for errors and get values
        self._read_user_configuration()
        # constructed nested plugins dict for storing betas and chd/mod
        self._build_plugins()
        # build the port map based off of the plugins which are not blacklsited
        self._build_port_map()
        # build a list of the background tasks based on those not in the blacklist
        self._build_background_tasks()
        # build and pickle the actual configuration object to be used in runtime
        self._pickle_self()

    def _read_user_configuration(self):
        # get the environment variables set by the user
        # raise warnings for incomplete file
        # generate template if no file exists
        if os.path.isfile(self.configuration_fn):
            user_config = yaml.load(stream=open(self.configuration_fn, 'r'))
            for plugin in user_config['ENVIRONMENT_VARIABLES']:
                try:
                    if user_config['BLACKLIST'][plugin]:
                        continue
                except KeyError:
                    # this happens when the key is 'Base'
                    print('Key Error {}'.format(plugin))
                    pass
                self._environment_variables[plugin] = OrderedDict()
                for k, v in user_config['ENVIRONMENT_VARIABLES'][plugin].items():
                    if v == '':
                        # TODO custom error
                        raise ValueError('The Environment Variable '
                                         '{ev} in Plugin {p} is not set'.format(ev=k,
                                                                                p=plugin))
                    else:
                        self._environment_variables[plugin][k] = v
        else:
            self._write_empty_configuration()
            # TODO custom error for missing config
            raise ValueError('No configuration file found. ' +
                             'A template has been generated for you.')

    def _write_empty_configuration(self):
        # when a user generated config has not been found, generate one
        # with some introspection information
        config = OrderedDict()
        # initialize empty blacklist
        config['BLACKLIST'] = {}

        # get base level environment variables
        config['ENVIRONMENT_VARIABLES'] = {}
        config['ENVIRONMENT_VARIABLES']['Base'] = {}
        with open(self.environment_fn, 'r') as f:
            for key in f.readlines():
                key = key.strip()
                config['ENVIRONMENT_VARIABLES']['Base'][key] = ''

        # iterate through plugin packages for environment variables
        plugins_dir = [os.getcwd(), 'Plugins']
        plugins_dir = os.path.join('', *plugins_dir)
        for name in os.listdir(plugins_dir):
            if name == '__pycache__':
                continue
            else:
                config['BLACKLIST'][name] = False
            config['ENVIRONMENT_VARIABLES'][name] = {}
            for f in os.listdir(os.path.join(plugins_dir, name)):
                if f == self.environment_fn:
                    with open(os.path.join(plugins_dir, name, f)) as environment_file:
                        ev_lines = environment_file.readlines()
                    for line in ev_lines:
                        key = line.strip()
                        config['ENVIRONMENT_VARIABLES'][name][key] = ''

        # iterate through background tasks for environment variables
        background_dir = [os.getcwd(), 'BackgroundTasks']
        background_dir = os.path.join('', *background_dir)
        for name in os.listdir(background_dir):
            if name == '__pycache__':
                continue
            else:
                config['BLACKLIST'][name] = False
            config['ENVIRONMENT_VARIABLES'][name] = {}
            for f in os.listdir(os.path.join(background_dir, name)):
                if f == self.environment_fn:
                    with open(os.path.join(background_dir, name, f)) as environment_file:
                        ev_lines = environment_file.readlines()
                    for line in ev_lines:
                        key = line.strip()
                        config['ENVIRONMENT_VARIABLES'][name][key] = ''
        yaml.dump(data=config,
                  stream=open(self.configuration_fn, 'w'))

    def _build_plugins(self):
        # iterate through keys of self.environment_variables to make nested plugin dict
        for key in self.environment_variables:
            if key == 'Base':
                continue
            elif key.endswith('Tasks'):
                continue
            self._plugins[key] = OrderedDict()
            self._plugins[key]['betas'] = OrderedDict()
            package_path = [os.getcwd(), 'Plugins', key]
            package_path = os.path.join('', *package_path)
            for f in os.listdir(package_path):
                if f.endswith('beta.py'):
                    beta_name = f.replace('.py', '')
                    self._plugins[key]['betas'][beta_name] = OrderedDict()
                    chd, mod = self._get_chd_and_mod(key, beta_name)
                    self._plugins[key]['betas'][beta_name]['command_hook_dict'] = chd
                    self._plugins[key]['betas'][beta_name]['modifiers'] = mod
                elif f.endswith('plugin.py'):
                    chd, mod = self._get_chd_and_mod(key)
                    self._plugins[key]['command_hook_dict'] = chd
                    self._plugins[key]['modifiers'] = mod

    def _build_background_tasks(self):
        for key in self.environment_variables:
            if key.endswith('Tasks'):
                self.background_tasks.append(key)

    def _build_port_map(self):
        # iterate through self.plugins to assign ports to plugins and betas
        PORT = 5555
        for key in self.plugins:
            self._port_map[key] = PORT
            PORT += 1

    def _get_chd_and_mod(self, plugin_name, beta_name=None):
        '''
        Retrieve command hook dict object from the given plugin or beta
        :param plugin_name: PluginName
        :param beta_name: test_beta
        :return:
        '''
        if beta_name is None:
            # get command hook for the main plugin
            # get snake case of plugin name for file
            snake_plugin_name = stringcase.snakecase(plugin_name)
            # Plugins.PluginName.plugin_name
            import_str = 'Plugins.{_dir}.{f}'.format(_dir=plugin_name,
                                                     f=snake_plugin_name)
            module = importlib.import_module(import_str)
            plugin = getattr(module, plugin_name)
            plugin = plugin()
            chd = getattr(plugin, 'COMMAND_HOOK_DICT')
            mod = getattr(plugin, 'MODIFIERS')
        else:
            # remove the .py
            import_str = 'Plugins.{_dir}.{f}'.format(_dir=plugin_name,
                                                     f=beta_name)
            module = importlib.import_module(import_str)
            beta = getattr(module, stringcase.pascalcase(beta_name))
            beta = beta()
            chd = getattr(beta, 'COMMAND_HOOK_DICT')
            mod = getattr(beta, 'MODIFIERS')
        return chd, mod

    def _pickle_self(self):
        pickle_path = [os.getcwd(), 'public_pickles', self.configuration_pickle_fn]
        pickle_path = os.path.join('', *pickle_path)
        pickle.dump(self, open(pickle_path, 'wb'))


if __name__ == "__main__":
    c = Configuration()
    c.make()
