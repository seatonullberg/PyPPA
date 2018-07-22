import os
import pickle
import importlib
import copy
import stringcase
from collections import OrderedDict


class Configuration(object):

    def __init__(self):
        self.port_map = OrderedDict()
        self.environment_variables = OrderedDict()
        self.plugins = OrderedDict()
        self.background_tasks = []

    @property
    def configuration_fn(self):
        return 'configuration.txt'

    @property
    def environment_fn(self):
        return 'environment.txt'

    def make(self):
        # build the configuration object and collect any errors
        self._scan_base()
        self._scan_plugins()
        self._scan_background_tasks()
        # all of the introspection is complete
        # compare to the user input config file
        self._compare_configuration()
        # either errors have been raised or the config was a success

    def _scan_base(self):
        # init the environment dict for base
        self.environment_variables['Base'] = OrderedDict()
        # scan the base environment file
        base_environment_fn = [os.getcwd(), self.environment_fn]
        base_environment_fn = os.path.join('', *base_environment_fn)
        with open(base_environment_fn, 'r') as f:
            lines = f.readlines()
        # fill the dict with keys
        for ev in lines:
            ev = ev.strip()
            self.environment_variables['Base'][ev] = None

    def _scan_plugins(self):
        # scan the plugin packages to collect all plugin information
        # name, command_hook_dict, modifiers, betas
        plugins_dir = [os.getcwd(), 'Plugins']
        plugins_dir = os.path.join('', *plugins_dir)
        for name in os.listdir(plugins_dir):
            if name == '__pycache__':
                pass
            self.environment_variables[name] = OrderedDict()
            self.environment_variables[name]['betas'] = OrderedDict()
            sub_plugin_dir = os.path.join(plugins_dir, name)
            # store plugins to do them last
            beta_file_names = []
            for f in os.listdir(sub_plugin_dir):
                # scan the environment file
                if f == self.environment_fn:
                    fname = os.path.join(sub_plugin_dir, f)
                    with open(fname, 'r') as environment_file:
                        lines = environment_file.readlines()
                    for ev in lines:
                        ev = ev.strip()
                        self.environment_variables[name][ev] = None
                # scan actual plugin file
                elif f.endswith('plugin.py'):
                    # get the actual command hook dict obj and modifiers objfrom the plugin
                    self._set_command_hook_dict_and_modifiers(plugin_name=name)
                elif f.endswith('beta.py'):
                    beta_file_names.append((name, f))

                else:
                    pass
            for plugin, beta in beta_file_names:
                # create a nested dict with betas command hook dict and modifiers
                self._set_command_hook_dict_and_modifiers(plugin_name=plugin,
                                                          beta_name=beta)

    def _set_command_hook_dict_and_modifiers(self, plugin_name, beta_name=None):
        '''
        Retrieve command hook dict object from the given plugin or beta
        :param plugin_name: PluginName
        :param beta_name: test_beta.py
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
            self.plugins[plugin_name] = OrderedDict()
            self.plugins[plugin_name]['command_hook_dict'] = chd
            self.plugins[plugin_name]['modifiers'] = mod
        else:
            # remove the .py
            beta_name = beta_name.split('.')[0]
            import_str = 'Plugins.{_dir}.{f}'.format(_dir=plugin_name,
                                                     f=beta_name)
            module = importlib.import_module(import_str)
            beta = getattr(module, stringcase.pascalcase(beta_name))
            beta = beta()
            chd = getattr(beta, 'COMMAND_HOOK_DICT')
            mod = getattr(beta, 'MODIFIERS')
            self.plugins[plugin_name]['betas'] = OrderedDict()
            self.plugins[plugin_name]['betas'][beta_name] = OrderedDict()
            self.plugins[plugin_name]['betas'][beta_name]['command_hook_dict'] = chd
            self.plugins[plugin_name]['betas'][beta_name]['modifiers'] = mod

    def _scan_background_tasks(self):
        # scan the background tasks for environment variables and names
        # store the names of the task modules
        background_tasks_dir = [os.getcwd(), 'BackgroundTasks']
        background_tasks_dir = os.path.join('', *background_tasks_dir)
        for name in os.listdir(background_tasks_dir):
            self.environment_variables[name] = OrderedDict()
            self.background_tasks.append(name)
            sub_background_task_dir = os.path.join(background_tasks_dir, name)
            for f in os.listdir(sub_background_task_dir):
                # scan the environment variables
                if f == self.environment_fn:
                    fname = os.path.join(sub_background_task_dir, f)
                    with open(fname, 'r') as environment_file:
                        lines = environment_file.readlines()
                    for ev in lines:
                        ev = ev.strip()
                        self.environment_variables[name][ev] = None

    def _compare_configuration(self):
        # compare the existing information to the user generated file
        try:
            with open(self.configuration_fn, 'r') as config_file:
                lines = config_file.readlines()
        except FileNotFoundError:
            # generate a new config file
            self._build_config_template()
            #TODO: make custom error for new configuration
            raise ValueError("No configuration set. A template has been generated.")
        else:
            # extract the configuration file information
            # remove blacklisted packages from contention
            blacklist = self._scan_config_blacklist(lines=lines)
            for b in blacklist:
                if b in self.environment_variables:
                    self.environment_variables.pop(b)
                if b in self.plugins:
                    self.plugins.pop(b)
                if b in self.background_tasks:
                    self.background_tasks = self.background_tasks - b
            user_config = OrderedDict()
            user_config = self._scan_config_environment_variables(config=user_config,
                                                                  lines=lines)
            user_config = self._scan_config_plugins(config=user_config,
                                                    lines=lines)
            user_config = self._scan_config_background_tasks(config=user_config,
                                                             lines=lines)

    def _build_config_template(self):
        # generate an empty configuration file
        template = OrderedDict()
        # blacklist is always initialized empty
        template['blacklist'] = '__BLACKLIST__\n'
        template['environment_variables'] = OrderedDict()
        # get base level environment variables first
        template['environment_variables']['Base'] = []
        template['plugins'] = OrderedDict()
        with open(self.environment_fn, 'r') as f:
            for key in f.readlines():
                ev = key.strip()
                template['environment_variables']['Base'].append(ev)
        # iterate through plugin packages for ev and names and betas
        plugins_dir = [os.getcwd(), 'Plugins']
        plugins_dir = os.path.join('', *plugins_dir)
        for name in os.listdir(plugins_dir):
            if name == '__pycache__':
                continue
            template['environment_variables'][name] = []
            # this list will store the associated beta files with the .py removed
            template['plugins'][name] = []
            for f in os.listdir(os.path.join(plugins_dir, name)):
                if f == 'environment.txt':
                    with open(os.path.join(plugins_dir, name, f)) as environment_file:
                        ev_lines = environment_file.readlines()
                    for line in ev_lines:
                        key = line.strip()
                        template['environment_variables'][name].append(key)
                elif f.endswith('beta.py'):
                    f = f.replace('.py', '')
                    beta = f.strip()
                    template['plugins'][name].append(beta)
                else:
                    continue
        # scan all background tasks for names
        template['background_tasks'] = []
        background_dir = [os.getcwd(), 'BackgroundTasks']
        background_dir = os.path.join('', *background_dir)
        for name in os.listdir(background_dir):
            if name == '__pycache__':
                continue
            name = name.strip()
            template['background_tasks'].append(name)

        # write the collected template to file
        with open(self.configuration_fn, 'w') as config_file:
            # write empty blacklist header
            config_file.write(template['blacklist'])
            # write environment variables header and keys
            config_file.write('__ENVIRONMENT_VARIABLES__\n')
            for key in template['environment_variables']:
                config_file.write(key+'\n')
                for ev in template['environment_variables'][key]:
                    config_file.write(ev+'\n')
                config_file.write('\n')
            # write plugin headers and betas
            config_file.write('__PLUGINS__\n')
            for key in template['plugins']:
                config_file.write(key+'\n')
                for beta in template['plugins'][key]:
                    config_file.write(beta+'\n')
                config_file.write('\n')
            # write backgroud task header and names
            config_file.write('__BACKGROUND_TASKS__\n')
            for task in template['background_tasks']:
                config_file.write(task+'\n')

    def _scan_config_blacklist(self, lines):
        blacklist = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line == '__BLACKLIST__':
                lines = lines[i+1:]
                i = 0
                l_init = lines[i]
                while not l_init.startswith('__'):
                    blacklist.append(l_init.strip())
                    i += 1
                    l_init = lines[i]
                break
        return blacklist

    def _scan_config_environment_variables(self, config, lines):
        config['environment_variables'] = OrderedDict()
        for i, line in enumerate(lines):
            line = line.strip()
            if line == '__ENVIRONMENT_VARIABLES__':
                lines = lines[i+1:]
                i = 0
                l_init = lines[i]
                # do loop to collect headers
                headers = []
                while not l_init.startswith('__'):
                    l_init = l_init.strip()
                    if '=' not in l_init:
                        headers.append(l_init)
                    i += 1
                    l_init = lines[i]
                # do loop to collect respective values
                i = 0
                l_init = lines[i]
                for h_index, h in enumerate(headers):
                    config['environment_variables'][h] = OrderedDict()
                    next_header = (headers[h_index] if h_index < len(headers) else headers[h_index-1])
                    while not l_init.startswith('__') and not next_header == l_init:
                        l_init = l_init.strip()
                        if '=' in l_init:
                            k, v = l_init.split('=')
                            config['environment_variables'][h][k] = v
                        i += 1
                        l_init = lines[i]
                break
        return config

    def _scan_config_plugins(self, config, lines):
        config['plugins'] = OrderedDict()
        for i, line in enumerate(lines):
            line = line.strip()
            if line == '__PLUGINS__':
                lines = lines[i+1:]
                i = 0
                l_init = lines[i]
                # do loop to collect headers
                headers = []
                while not l_init.startswith('__'):
                    l_init = l_init.strip()
                    if l_init.endswith('Plugin'):
                        headers.append(l_init)
                    i += 1
                    l_init = lines[i]
                # do loop to collect respective values
                i = 0
                l_init = lines[i]
                for h_index, h in enumerate(headers):
                    config['plugins'][h] = OrderedDict()
                    next_header = (headers[h_index] if h_index < len(headers) else headers[h_index - 1])
                    while not l_init.startswith('__') and not next_header == l_init:
                        l_init = l_init.strip()
                        if l_init.endswith('beta'):
                            config['plugins'][h][l_init] = OrderedDict()
                        i += 1
                        l_init = lines[i]
                break
        return config

    def _scan_config_background_tasks(self, config, lines):
        config['background_tasks'] = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line == '__BACKGROUND_TASKS__':
                lines = lines[i + 1:]
                i = 0
                l_init = lines[i]
                # do loop to collect task names
                while not l_init.startswith('__'):
                    l_init = l_init.strip()
                    if l_init.endswith('Tasks'):
                        config['background_tasks'].append(l_init)
                    i += 1
                    # TODO: not clean
                    try:
                        l_init = lines[i]
                    except IndexError:
                        break

                break
        return config


if __name__ == "__main__":
    c = Configuration()
    c.make()
